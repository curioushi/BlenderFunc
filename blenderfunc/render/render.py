import os
import bpy
import addon_utils


def render_color(filepath: str = '/tmp/temp.png', samples: int = 32, auto_tile_size: bool = True,
                 denoiser: str = None, num_threads: int = 1, simplify_subdivision_render: int = 3,
                 diffuse_bounces: int = 3, glossy_bounces: int = 0, ao_bounces_render: int = 3, max_bounces: int = 3,
                 transmission_bounces: int = 0, transparent_max_bounces: int = 8, volume_bounces: int = 0):
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
    if denoiser.upper() in ['NLM', 'OPTIX', 'OPENIMAGEDENOISE']:
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
    file_output_node.file_slots['Image'].path = ''
    node_tree.links.new(render_layers_node.outputs[0], file_output_node.inputs[0])
    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(use_viewport=True)

    os.rename(os.path.join(output_dir, '0001.png'), filepath)
    print('image saved: {}'.format(filepath))


__all__ = ['render_color']
