import os
import bpy


def render_color(filepath='/tmp/temp.png'):
    scene = bpy.data.scenes['Scene']
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.use_nodes = True
    node_tree = scene.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)

    output_dir = os.path.dirname(filepath)
    # TODO: support more output image format

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
