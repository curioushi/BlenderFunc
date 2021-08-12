import os
import bpy
import addon_utils
import imageio
import numpy as np
from blenderfunc.object.texture import load_image


def render_color(filepath: str = '/tmp/temp.png', samples: int = 32, color_mode: str = 'RGB', color_depth: int = '8',
                 auto_tile_size: bool = True, denoiser: str = None, num_threads: int = 1,
                 simplify_subdivision_render: int = 3, diffuse_bounces: int = 3, glossy_bounces: int = 0,
                 ao_bounces_render: int = 3, max_bounces: int = 3, transmission_bounces: int = 0,
                 transparent_max_bounces: int = 8, volume_bounces: int = 0):
    addon_utils.enable("render_auto_tile_size")
    scene = bpy.data.scenes['Scene']
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = samples
    scene.cycles.debug_bvh_type = "STATIC_BVH"
    scene.cycles.debug_use_spatial_splits = True
    scene.render.use_persistent_data = True
    if auto_tile_size:
        scene.ats_settings.is_enable = True
    else:
        scene.ats_settings.is_enable = False
    if denoiser is not None and denoiser.upper() in ['NLM', 'OPTIX', 'OPENIMAGEDENOISE']:
        bpy.context.view_layer.cycles.use_denoising = True
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = denoiser.upper()
    else:
        bpy.context.view_layer.cycles.use_denoising = False
        scene.cycles.use_denoising = False
    if num_threads > 0:
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 1
    else:
        scene.render.threads_mode = 'AUTO'
    if simplify_subdivision_render > 0:
        scene.render.use_simplify = True
        scene.render.simplify_subdivision_render = simplify_subdivision_render
    else:
        scene.render.use_simplify = False
    scene.cycles.diffuse_bounces = diffuse_bounces
    scene.cycles.glossy_bounces = glossy_bounces
    scene.cycles.ao_bounces_render = ao_bounces_render
    scene.cycles.max_bounces = max_bounces
    scene.cycles.transmission_bounces = transmission_bounces
    scene.cycles.transparent_max_bounces = transparent_max_bounces
    scene.cycles.volume_bounces = volume_bounces

    output_dir = os.path.dirname(filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = os.path.dirname(filepath)
    file_output_node.file_slots['Image'].path = 'image'
    if color_mode in ['BW', 'RGB', 'RGBA']:
        file_output_node.format.color_mode = color_mode
    if color_depth in ['8', '16']:
        file_output_node.format.color_depth = color_depth
    node_tree.links.new(render_layers_node.outputs[0], file_output_node.inputs[0])
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    os.rename(os.path.join(output_dir, 'image0001.png'), filepath)
    print('image saved: {}'.format(filepath))


def render_shadow_mask(filepath: str = '/tmp/temp.png', light: bpy.types.Object = None):
    # remove background light
    world = bpy.data.worlds.get('World', None)
    if world:
        world.cycles_visibility.camera = False
        world.cycles_visibility.diffuse = False
        world.cycles_visibility.glossy = False
        world.cycles_visibility.transmission = False
        world.cycles_visibility.scatter = False

    # hide other light sources
    other_lights = []
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and obj != light:
            other_lights.append(obj)
            obj.hide_render = True

    light.data.energy = 10000000
    light.data.shadow_soft_size = 0
    light.data.cycles.max_bounces = 0
    light.data.cycles.cast_shadow = True
    if light.data.use_nodes:
        tree = light.data.node_tree
        tree.nodes['Image Texture'].image = load_image('resources/images/white.png')

    addon_utils.enable("render_auto_tile_size")
    scene = bpy.data.scenes['Scene']
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 1
    scene.cycles.debug_bvh_type = "STATIC_BVH"
    scene.cycles.debug_use_spatial_splits = True
    scene.render.use_persistent_data = True
    scene.ats_settings.is_enable = True
    bpy.context.view_layer.cycles.use_denoising = False
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 1
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.cycles.ao_bounces_render = 0
    scene.cycles.max_bounces = 0
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 0
    scene.cycles.volume_bounces = 0

    output_dir = os.path.dirname(filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = os.path.dirname(filepath)
    file_output_node.file_slots['Image'].path = 'image'
    file_output_node.format.color_mode = 'BW'
    file_output_node.format.color_depth = '8'
    node_tree.links.new(render_layers_node.outputs[0], file_output_node.inputs[0])
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    output_png = os.path.join(output_dir, 'image0001.png')
    mask = imageio.imread(output_png)
    if mask.ndim == 3:
        mask = mask[:, :, 0]
    mask = np.array((mask > 122) * 255).astype(np.uint8)
    imageio.imwrite(filepath, mask)
    print('image saved: {}'.format(filepath))
    os.remove(output_png)

    # unset visibility
    other_lights = []
    for obj in other_lights:
        obj.hide_render = False

    if world:
        world.cycles_visibility.camera = True
        world.cycles_visibility.diffuse = True
        world.cycles_visibility.glossy = True
        world.cycles_visibility.transmission = True
        world.cycles_visibility.scatter = True


def render_depth(filepath: str = '/tmp/temp.png', depth_scale=0.00005):
    addon_utils.enable("render_auto_tile_size")
    scene = bpy.data.scenes['Scene']
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 1
    scene.cycles.debug_bvh_type = "STATIC_BVH"
    scene.cycles.debug_use_spatial_splits = True
    scene.render.use_persistent_data = True
    scene.ats_settings.is_enable = True
    bpy.context.view_layer.cycles.use_denoising = False
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 1
    scene.render.use_simplify = True
    scene.render.simplify_subdivision_render = 3
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.cycles.ao_bounces_render = 0
    scene.cycles.max_bounces = 0
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 0
    scene.cycles.volume_bounces = 0

    output_dir = os.path.dirname(filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    render_layers_node = node_tree.nodes.new('CompositorNodeRLayers')
    file_output_node = node_tree.nodes.new('CompositorNodeOutputFile')
    file_output_node.base_path = os.path.dirname(filepath)
    file_output_node.file_slots['Image'].path = 'image'
    file_output_node.format.file_format = 'OPEN_EXR'
    node_tree.links.new(render_layers_node.outputs[2], file_output_node.inputs[0])
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    output_exr = os.path.join(output_dir, 'image0001.exr')
    depth = imageio.imread(output_exr)
    depth = depth[:, :, 0]
    depth = depth / depth_scale
    depth = depth.astype(np.uint16)
    imageio.imwrite(filepath, depth)
    print('image saved: {}'.format(filepath))
    os.remove(output_exr)


__all__ = ['render_color', 'render_depth', 'render_shadow_mask']
