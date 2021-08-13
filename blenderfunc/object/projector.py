import os
from typing import List

import bpy
from PIL import Image
from mathutils import Matrix


def set_projector(opencv_matrix: List[List[float]] = None,
                  image_path: str = None,
                  pose: List[List[float]] = None,
                  energy: float = 100.0,
                  flip_x: bool = False,
                  flip_y: bool = False,
                  max_bounces: int = 0) -> str:
    if opencv_matrix is None:
        opencv_matrix = [[512, 0, 256], [0, 512, 256], [0, 0, 1]]
    if image_path is None:
        image_path = 'resources/images/test.png'
    if pose is None:
        pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 1], [0, 0, 0, 1]]

    # remove all projector lights
    for light in bpy.data.lights:
        if light.use_nodes:
            bpy.data.lights.remove(light)

    bpy.ops.object.light_add(type='SPOT')
    projector = bpy.context.active_object
    projector.name = 'Projector'
    Q = Matrix([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    projector.matrix_world = Matrix(pose) @ Q

    projector.data.name = 'Projector'
    projector.data.energy = energy
    projector.data.cycles.max_bounces = max_bounces
    projector.data.distance = 0
    projector.data.spot_size = 1.5
    projector.data.shadow_soft_size = 0
    projector.data.use_nodes = True

    # build node
    node_tree = projector.data.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)
    node_texcoord = node_tree.nodes.new('ShaderNodeTexCoord')
    node_texcoord.location = (0, 0)
    node_separate = node_tree.nodes.new('ShaderNodeSeparateXYZ')
    node_separate.location = (400, -300)
    node_abs = node_tree.nodes.new('ShaderNodeMath')
    node_abs.location = (400, -150)
    node_abs.operation = 'ABSOLUTE'
    node_mul = node_tree.nodes.new('ShaderNodeVectorMath')
    node_mul.operation = 'MULTIPLY'
    node_mul.location = (200, 0)
    node_mul.inputs[1].default_value[0] = 1.0
    node_mul.inputs[1].default_value[1] = 1.0
    node_mul.inputs[1].default_value[2] = 1.0
    node_divide = node_tree.nodes.new('ShaderNodeVectorMath')
    node_divide.operation = 'DIVIDE'
    node_divide.location = (400, 0)
    node_mapping = node_tree.nodes.new('ShaderNodeMapping')
    node_mapping.location = (600, 0)
    node_teximg = node_tree.nodes.new('ShaderNodeTexImage')
    bpy.ops.image.open(filepath=os.path.abspath(image_path), relative_path=False)
    image_texture = bpy.data.images[os.path.basename(image_path)]
    node_teximg.image = image_texture
    node_teximg.extension = 'CLIP'
    node_teximg.image_user.use_cyclic = True
    node_teximg.image_user.use_auto_refresh = True
    node_teximg.location = (800, 0)
    node_emission = node_tree.nodes.new('ShaderNodeEmission')
    node_emission.location = (1100, 0)
    node_output = node_tree.nodes.new('ShaderNodeOutputLight')
    node_output.location = (1100, -200)
    node_tree.links.new(node_texcoord.outputs[1], node_separate.inputs[0])
    node_tree.links.new(node_texcoord.outputs[1], node_mul.inputs[0])
    node_tree.links.new(node_mul.outputs[0], node_divide.inputs[0])
    node_tree.links.new(node_separate.outputs[2], node_abs.inputs[0])
    node_tree.links.new(node_abs.outputs[0], node_divide.inputs[1])
    node_tree.links.new(node_divide.outputs[0], node_mapping.inputs[0])
    node_tree.links.new(node_mapping.outputs[0], node_teximg.inputs[0])
    node_tree.links.new(node_teximg.outputs[0], node_emission.inputs[0])
    node_tree.links.new(node_emission.outputs[0], node_output.inputs[0])

    fx = opencv_matrix[0][0]
    fy = opencv_matrix[1][1]
    cx = opencv_matrix[0][2]
    cy = opencv_matrix[1][2]
    img = Image.open(image_path)
    width, height = img.size

    # location
    node_mapping.inputs[1].default_value[0] = (cx + 0.5) / width
    node_mapping.inputs[1].default_value[1] = (cy + 0.5) / height
    # scale
    node_mapping.inputs[3].default_value[0] = fx / width
    node_mapping.inputs[3].default_value[1] = fy / height

    # flip
    if flip_x:
        node_mul.inputs[1].default_value[0] = -1.0
        node_mapping.inputs[1].default_value[0] = 1 - node_mapping.inputs[1].default_value[0]
    if flip_y:
        node_mul.inputs[1].default_value[1] = -1.0
        node_mapping.inputs[1].default_value[1] = 1 - node_mapping.inputs[1].default_value[1]
    return projector.name


__all__ = ['set_projector']
