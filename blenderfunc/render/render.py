import os
import cv2
import bpy
import addon_utils
import imageio
import time
import random
import numpy as np
from typing import List
from blenderfunc.object.texture import load_image
from blenderfunc.utility.initialize import remove_all_materials, set_background_light
from blenderfunc.utility.utility import save_blend, get_object_by_name
from blenderfunc.object.collector import get_all_mesh_objects


def _distort_image(image: np.ndarray):
    camera_objs = []
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            camera_objs.append(obj)
    if len(camera_objs) != 1:
        raise Exception('Number of camera objects should be one')
    cam_ob = camera_objs[0]
    camera_matrix = cam_ob.get('CameraMatrix', None)
    distort_coeffs = cam_ob.get('DistortCoeffs', None)
    if camera_matrix is None or distort_coeffs is None:
        raise Exception('Camera should have custom properties: "CameraMatrix" and "DistortCoeffs"')
    camera_matrix = np.array(camera_matrix, dtype=np.float32)
    distort_coeffs = np.array(distort_coeffs, dtype=np.float32)
    if np.all(distort_coeffs == 0):
        return image, False

    # distort image
    pts = np.zeros(image.shape[:2] + (2,), dtype=np.float32)
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            pts[y, x, 0] = x
            pts[y, x, 1] = y
    distort_pts = cv2.undistortPoints(pts.reshape(-1, 2), cameraMatrix=camera_matrix,
                                      distCoeffs=distort_coeffs, R=None, P=camera_matrix)
    distort_pts = distort_pts.reshape(*pts.shape)
    map_x = distort_pts[:, :, 0]
    map_y = distort_pts[:, :, 1]
    distorted_image = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
    return distorted_image, True


def _initialize_renderer(samples: int = 32, denoiser: str = None, max_bounces: int = 3, auto_tile_size: bool = True,
                         num_threads: int = 1, simplify_subdivision_render: int = 3):
    cprefs = bpy.context.preferences.addons['cycles'].preferences
    cprefs.get_devices()
    cprefs.compute_device_type = 'CUDA'
    scene = bpy.data.scenes['Scene']
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = samples
    scene.cycles.debug_bvh_type = "STATIC_BVH"
    scene.cycles.debug_use_spatial_splits = True
    scene.render.use_persistent_data = True

    if denoiser is not None and denoiser.upper() in ['NLM', 'OPTIX', 'OPENIMAGEDENOISE']:
        bpy.context.view_layer.cycles.use_denoising = True
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = denoiser.upper()
    else:
        bpy.context.view_layer.cycles.use_denoising = False
        scene.cycles.use_denoising = False

    scene.cycles.diffuse_bounces = max_bounces
    scene.cycles.glossy_bounces = max_bounces
    scene.cycles.ao_bounces_render = max_bounces
    scene.cycles.max_bounces = max_bounces
    scene.cycles.transmission_bounces = max_bounces
    scene.cycles.transparent_max_bounces = max_bounces
    scene.cycles.volume_bounces = max_bounces

    addon_utils.enable("render_auto_tile_size")
    if auto_tile_size:
        scene.ats_settings.is_enable = True
    else:
        scene.ats_settings.is_enable = False

    if num_threads > 0:
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 1
    else:
        scene.render.threads_mode = 'AUTO'

    scene.render.use_simplify = True
    scene.render.simplify_subdivision_render = simplify_subdivision_render


def render_color(filepath: str = '/tmp/temp.png', save_blend_file: bool = False,
                 samples: int = 32, denoiser: str = None, max_bounces: int = 3, color_mode: str = 'RGB',
                 color_depth: int = '8', auto_tile_size: bool = True, num_threads: int = 1):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_color()')

    _initialize_renderer(samples, denoiser, max_bounces, auto_tile_size, num_threads)

    # make output folder
    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # make node tree
    scene = bpy.data.scenes['Scene']
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = output_dir
    file_output_node.file_slots['Image'].path = 'image'
    if color_mode in ['BW', 'RGB', 'RGBA']:
        file_output_node.format.color_mode = color_mode
    if color_depth in ['8', '16']:
        file_output_node.format.color_depth = color_depth
    node_tree.links.new(render_layers_node.outputs['Image'], file_output_node.inputs['Image'])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # rename output
    os.rename(os.path.join(output_dir, 'image0001.png'), filepath)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    distort_img, changed = _distort_image(imageio.imread(filepath))
    if changed:
        imageio.imwrite(filepath, distort_img, compression=3)

    bpy.ops.ed.undo_push(message='after render_color()')
    bpy.ops.ed.undo()


def apply_nan_mask(filepath: str, maskpath: str, outputpath: str = None):
    image = imageio.imread(filepath)
    mask = imageio.imread(maskpath) < 127
    image[mask] = 0
    if outputpath is None:
        imageio.imwrite(filepath, image)
    else:
        imageio.imwrite(outputpath, image)


def render_light_mask(filepath: str = '/tmp/temp.png', light_name: str = '', cast_shadow: bool = True,
                      energy: float = 100, threshold: float = 0.0, save_blend_file: bool = False):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))
    light = get_object_by_name(light_name)

    bpy.ops.ed.undo_push(message='before render_shadow_mask()')

    _initialize_renderer(samples=32, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

    # hide all other light sources
    world = bpy.data.worlds.get('World', None)
    if world:
        world.cycles_visibility.camera = False
        world.cycles_visibility.diffuse = False
        world.cycles_visibility.glossy = False
        world.cycles_visibility.transmission = False
        world.cycles_visibility.scatter = False

    other_lights = []
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and obj != light:
            other_lights.append(obj)
            obj.hide_render = True

    # increase light power
    light.data.energy = energy
    light.data.shadow_soft_size = 0
    light.data.cycles.max_bounces = 0
    light.data.cycles.cast_shadow = cast_shadow
    if light.data.use_nodes:
        tree = light.data.node_tree
        tree.nodes['Image Texture'].image = load_image('resources/images/white.png')

    # maximize roughness
    remove_all_materials()
    for mesh in bpy.data.meshes:
        mat = bpy.data.materials.new("Material")
        mat.use_nodes = True
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1.0
        mesh.materials.clear()
        mesh.materials.append(mat)

    # make output folder
    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # make node tree
    scene = bpy.data.scenes['Scene']
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    n_render_layer = node_tree.nodes.new('CompositorNodeRLayers')
    n_render_layer.location = (0, 0)

    n_rgb2bw = node_tree.nodes.new('CompositorNodeRGBToBW')
    n_rgb2bw.location = (300, 0)

    n_normalize = node_tree.nodes.new('CompositorNodeNormalize')
    n_normalize.location = (500, 0)

    n_threshold = node_tree.nodes.new('CompositorNodeMath')
    n_threshold.operation = 'GREATER_THAN'
    n_threshold.inputs[1].default_value = threshold
    n_threshold.location = (700, 0)

    n_file_output = node_tree.nodes.new('CompositorNodeOutputFile')
    n_file_output.location = (900, 0)
    n_file_output.base_path = output_dir
    n_file_output.file_slots['Image'].path = 'image'
    n_file_output.format.color_mode = 'BW'
    n_file_output.format.color_depth = '8'

    node_tree.links.new(n_render_layer.outputs[0], n_rgb2bw.inputs[0])
    node_tree.links.new(n_rgb2bw.outputs[0], n_normalize.inputs[0])
    node_tree.links.new(n_normalize.outputs[0], n_threshold.inputs[0])
    node_tree.links.new(n_threshold.outputs[0], n_file_output.inputs[0])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # postprocess
    temp_output = os.path.join(output_dir, 'image0001.png')
    os.rename(temp_output, filepath)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='after render_shadow_mask()')
    bpy.ops.ed.undo()


def render_depth(filepath: str = '/tmp/temp.png', depth_scale=0.00005, save_blend_file=False, save_npz=True):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_depth()')

    _initialize_renderer(samples=50, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

    # make output folder
    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # make node tree
    scene = bpy.data.scenes['Scene']
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = output_dir
    file_output_node.file_slots['Image'].path = 'image'
    file_output_node.format.file_format = 'OPEN_EXR'
    node_tree.links.new(render_layers_node.outputs[2], file_output_node.inputs[0])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # postprocess
    temp_output = os.path.join(output_dir, 'image0001.exr')
    depth = imageio.imread(temp_output)
    depth = depth[:, :, 0]
    depth[depth > 10] = float('nan')
    depth, _ = _distort_image(depth)
    if save_npz:
        np.savez_compressed(os.path.splitext(filepath)[0] + '.npz', data=depth)
    depth = depth / depth_scale
    depth = depth.astype(np.uint16)
    imageio.imwrite(filepath, depth, compression=3)
    os.remove(temp_output)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='before render_depth()')
    bpy.ops.ed.undo()


def _compute_index_color_map(indices: List[int]):
    """ compute the mapping from index to color_center, color_min, color_max"""
    num = len(indices)
    n_splits_per_dim = 1
    while n_splits_per_dim ** 3 < num:
        n_splits_per_dim += 1

    block_size = 1 / n_splits_per_dim
    half_size = block_size / 2
    linspace = [half_size + i * block_size for i in range(n_splits_per_dim)]
    color_center = []
    for r in range(n_splits_per_dim):
        for g in range(n_splits_per_dim):
            for b in range(n_splits_per_dim):
                color_center.append([linspace[r], linspace[g], linspace[b]])
    color_center = np.array(color_center)
    color_min = color_center - np.array([half_size, half_size, half_size])
    color_max = color_center + np.array([half_size, half_size, half_size])
    color_center = color_center.tolist()
    color_min = color_min.tolist()
    color_max = color_max.tolist()
    mapping = {indices[i]: dict(color=color_center[i], min=color_min[i], max=color_max[i]) for i in range(num)}
    return mapping


def _color2segmap(color: np.ndarray, index_color_map: dict):
    r = color[:, :, 0]
    g = color[:, :, 1]
    b = color[:, :, 2]
    segmap = np.zeros(color.shape[:2], dtype=np.int)
    for index, val in index_color_map.items():
        color_min = val['min']
        color_max = val['max']
        bool_mask = (r > color_min[0]) & (r < color_max[0]) & (g > color_min[1]) & (g < color_max[1]) & (
                b > color_min[2]) & (b < color_max[2])
        segmap[bool_mask] = index
    return segmap


def render_instance_segmap(filepath: str = '/tmp/temp.png', save_blend_file=False, save_npz=True):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_instance_segmap()')

    _initialize_renderer(samples=10, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

    mesh_objects = get_all_mesh_objects()
    num = len(mesh_objects) + 1  # for background
    index_color_map = _compute_index_color_map([i for i in range(num)])

    # set color for background
    set_background_light(color=index_color_map[0]['color'])

    # set color for each object
    remove_all_materials()
    for i, obj in enumerate(mesh_objects):
        mesh = obj.data.copy()
        obj.data = mesh
        mat = bpy.data.materials.new('Material')
        mat.use_nodes = True
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.remove(nodes['Principled BSDF'])
        n_emission = nodes.new('ShaderNodeEmission')
        n_output = nodes['Material Output']
        links.new(n_emission.outputs['Emission'], n_output.inputs['Surface'])
        color = index_color_map[i + 1]['color']
        n_emission.inputs['Color'].default_value[0] = color[0]
        n_emission.inputs['Color'].default_value[1] = color[1]
        n_emission.inputs['Color'].default_value[2] = color[2]
        mesh.materials.clear()
        mesh.materials.append(mat)

    # make output dir
    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # make node tree
    scene = bpy.data.scenes['Scene']
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = output_dir
    file_output_node.file_slots['Image'].path = 'image'
    file_output_node.format.file_format = 'OPEN_EXR'
    file_output_node.format.color_mode = 'RGB'
    file_output_node.format.color_depth = '32'
    node_tree.links.new(render_layers_node.outputs['Image'], file_output_node.inputs['Image'])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # save visualization image
    temp_output = os.path.join(output_dir, 'image0001.exr')
    color_segmap = imageio.imread(temp_output)
    color_segmap, _ = _distort_image(color_segmap)
    os.remove(temp_output)
    vis = (color_segmap * 255).astype(np.uint8)
    imageio.imwrite(filepath, vis, compression=3)

    # save numpy data
    segmap = _color2segmap(color_segmap, index_color_map)
    if save_npz:
        np.savez_compressed(os.path.splitext(filepath)[0] + '.npz', data=segmap)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='after render_instance_segmap()')
    bpy.ops.ed.undo()


def render_class_segmap(filepath: str = '/tmp/temp.png', save_blend_file=False, save_npz=True):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_class_segmap()')

    _initialize_renderer(samples=10, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

    mesh_objects = get_all_mesh_objects()
    class_indices = [0]  # zero for unknown class
    for obj in mesh_objects:
        class_indices.append(obj.get('class_id', 0))
    class_indices = sorted(list(set(class_indices)))
    index_color_map = _compute_index_color_map(class_indices)
    print(index_color_map)

    # set color for background
    set_background_light(color=index_color_map[0]['color'])

    # set color for each object
    remove_all_materials()
    for obj in mesh_objects:
        mesh = obj.data.copy()
        obj.data = mesh
        mat = bpy.data.materials.new('Material')
        mat.use_nodes = True
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.remove(nodes['Principled BSDF'])
        n_emission = nodes.new('ShaderNodeEmission')
        n_output = nodes['Material Output']
        links.new(n_emission.outputs['Emission'], n_output.inputs['Surface'])
        index = obj.get('class_id', 0)
        color = index_color_map[index]['color']
        n_emission.inputs['Color'].default_value[0] = color[0]
        n_emission.inputs['Color'].default_value[1] = color[1]
        n_emission.inputs['Color'].default_value[2] = color[2]
        mesh.materials.clear()
        mesh.materials.append(mat)

    # make output dir
    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # make node tree
    scene = bpy.data.scenes['Scene']
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = output_dir
    file_output_node.file_slots['Image'].path = 'image'
    file_output_node.format.file_format = 'OPEN_EXR'
    file_output_node.format.color_mode = 'RGB'
    file_output_node.format.color_depth = '32'
    node_tree.links.new(render_layers_node.outputs['Image'], file_output_node.inputs['Image'])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # save visualization mage
    temp_output = os.path.join(output_dir, 'image0001.exr')
    color_segmap = imageio.imread(temp_output)
    color_segmap, _ = _distort_image(color_segmap)
    os.remove(temp_output)
    vis = (color_segmap * 255).astype(np.uint8)
    imageio.imwrite(filepath, vis, compression=3)

    # save numpy data
    segmap = _color2segmap(color_segmap, index_color_map)
    if save_npz:
        np.savez_compressed(os.path.splitext(filepath)[0] + '.npz', data=segmap)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='after render_class_segmap()')
    bpy.ops.ed.undo()


def render_normal_map(filepath: str = '/tmp/temp.png', save_blend_file=False, save_npz=True):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_normal_map()')

    _initialize_renderer(samples=50, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

    set_background_light(strength=0)

    # set material for all meshes
    for mesh in bpy.data.meshes:
        mat = bpy.data.materials.new('Material')
        mat.use_nodes = True
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.remove(nodes['Principled BSDF'])
        n_emission = nodes.new('ShaderNodeEmission')
        n_normal_map = nodes.new('ShaderNodeNormalMap')
        n_output = nodes['Material Output']
        links.new(n_normal_map.outputs['Normal'], n_emission.inputs['Color'])
        links.new(n_emission.outputs['Emission'], n_output.inputs['Surface'])
        mesh.materials.clear()
        mesh.materials.append(mat)

    # make output dir
    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # make node tree
    scene = bpy.data.scenes['Scene']
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = output_dir
    file_output_node.file_slots['Image'].path = 'image'
    file_output_node.format.file_format = 'OPEN_EXR'
    file_output_node.format.color_mode = 'RGB'
    file_output_node.format.color_depth = '32'
    node_tree.links.new(render_layers_node.outputs['Image'], file_output_node.inputs['Image'])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # save visualization mage
    temp_output = os.path.join(output_dir, 'image0001.exr')
    normal = imageio.imread(temp_output)
    normal, _ = _distort_image(normal)
    os.remove(temp_output)
    vis = ((normal / 2 + 0.5) * 255).astype(np.uint8)
    imageio.imwrite(filepath, vis, compression=3)

    # save numpy data
    if save_npz:
        np.savez_compressed(os.path.splitext(filepath)[0] + '.npz', data=normal)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='after render_normal_map()')
    bpy.ops.ed.undo()


__all__ = ['render_color', 'render_depth', 'render_light_mask', 'render_instance_segmap', 'render_class_segmap',
           'render_normal_map', 'apply_nan_mask']
