import os
import bpy
import addon_utils
import imageio
import random
import numpy as np
from blenderfunc.object.texture import load_image
from blenderfunc.utility.initialize import remove_all_materials
from blenderfunc.utility.utility import save_blend, get_object_by_name
from blenderfunc.object.collector import get_all_mesh_objects


def _initialize_renderer(samples: int = 32, denoiser: str = None, max_bounces: int = 3, auto_tile_size: bool = True,
                         num_threads: int = 1, simplify_subdivision_render: int = 3):
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


def render_color(filepath: str = '/tmp/temp.png', save_blend_file: bool = False, samples: int = 32,
                 color_mode: str = 'RGB', color_depth: int = '8', auto_tile_size: bool = True, denoiser: str = None,
                 num_threads: int = 1, max_bounces: int = 3):
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

    bpy.ops.ed.undo_push(message='after render_color()')
    bpy.ops.ed.undo()


def render_shadow_mask(filepath: str = '/tmp/temp.png', light_name: str = '', save_blend_file: bool = False):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))
    light = get_object_by_name(light_name)

    bpy.ops.ed.undo_push(message='before render_shadow_mask()')

    _initialize_renderer(samples=1, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

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
    light.data.energy = 10000000
    light.data.shadow_soft_size = 0
    light.data.cycles.max_bounces = 0
    light.data.cycles.cast_shadow = True
    if light.data.use_nodes:
        tree = light.data.node_tree
        tree.nodes['Image Texture'].image = load_image('resources/images/white.png')

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
    file_output_node.format.color_mode = 'BW'
    file_output_node.format.color_depth = '8'
    node_tree.links.new(render_layers_node.outputs[0], file_output_node.inputs[0])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # postprocess
    temp_output = os.path.join(output_dir, 'image0001.png')
    mask = imageio.imread(temp_output)
    if mask.ndim == 3:
        mask = mask[:, :, 0]
    mask = np.array((mask > 122) * 255).astype(np.uint8)
    imageio.imwrite(filepath, mask)
    os.remove(temp_output)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='after render_shadow_mask()')
    bpy.ops.ed.undo()


def render_depth(filepath: str = '/tmp/temp.png', depth_scale=0.00005, save_blend_file=False):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_depth()')

    _initialize_renderer(samples=1, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

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
    depth = depth / depth_scale
    depth = depth.astype(np.uint16)
    imageio.imwrite(filepath, depth)
    os.remove(temp_output)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='before render_depth()')
    bpy.ops.ed.undo()


def render_instance_segmap(filepath: str = '/tmp/temp.png', save_blend_file=False):
    if os.path.splitext(filepath)[-1] not in ['.png']:
        raise Exception('Unsupported image format: {}'.format(os.path.splitext(filepath)))

    bpy.ops.ed.undo_push(message='before render_instance_segmap()')

    _initialize_renderer(samples=1, denoiser=None, max_bounces=0, auto_tile_size=True, num_threads=1)

    remove_all_materials()

    # copy mesh objects
    for obj in get_all_mesh_objects():
        mesh = obj.data.copy()
        obj.data = mesh

    # set material
    for mesh in bpy.data.meshes:
        mat = bpy.data.materials.new('Material')
        mat.use_nodes = True
        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links
        nodes.remove(nodes['Principled BSDF'])
        n_emission = nodes.new('ShaderNodeEmission')
        n_output = nodes['Material Output']
        links.new(n_emission.outputs['Emission'], n_output.inputs['Surface'])
        n_emission.inputs['Color'].default_value[0] = random.random()
        n_emission.inputs['Color'].default_value[1] = random.random()
        n_emission.inputs['Color'].default_value[2] = random.random()
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
    file_output_node.format.file_format = 'PNG'
    file_output_node.format.color_mode = 'RGB'
    node_tree.links.new(render_layers_node.outputs['Image'], file_output_node.inputs['Image'])

    # render
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    # postprocess
    os.rename(os.path.join(output_dir, 'image0001.png'), filepath)
    print('image saved: {}'.format(filepath))

    if save_blend_file:
        save_blend(os.path.splitext(filepath)[0] + '.blend')

    bpy.ops.ed.undo_push(message='after render_instance_segmap()')
    bpy.ops.ed.undo()


__all__ = ['render_color', 'render_depth', 'render_shadow_mask', 'render_instance_segmap']
