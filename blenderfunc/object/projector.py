import os
from typing import List

import bpy
from PIL import Image
from mathutils import Matrix


def _new_distortion_node_group(name: str = "DistortionNodeGroup", k1: float = 0.0, k2: float = 0.0, k3: float = 0.0,
                               p1: float = 0.0, p2: float = 0.0):
    group = bpy.data.node_groups.get(name, None)
    if group is None:
        group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
        group.inputs.new('NodeSocketVector', 'Vector')
        group.inputs.new('NodeSocketFloat', 'k1')
        group.inputs.new('NodeSocketFloat', 'k2')
        group.inputs.new('NodeSocketFloat', 'k3')
        group.inputs.new('NodeSocketFloat', 'p1')
        group.inputs.new('NodeSocketFloat', 'p2')
        group.outputs.new('NodeSocketVector', 'Vector')

        input_node = group.nodes.new("NodeGroupInput")
        input_node.location = (0, 0)

        node_mapping1 = group.nodes.new('ShaderNodeMapping')
        node_mapping1.location = (0, 400)
        node_mapping1.inputs['Scale'].default_value[1] = -1  # flip y-axis

        node_separate = group.nodes.new('ShaderNodeSeparateXYZ')
        node_separate.location = (200, 0)

        # x2,y2,xy
        node_x2 = group.nodes.new('ShaderNodeMath')
        node_x2.location = (400, 0)
        node_x2.operation = 'MULTIPLY'
        node_x2.label = 'x^2'

        node_y2 = group.nodes.new('ShaderNodeMath')
        node_y2.location = (400, -200)
        node_y2.operation = 'MULTIPLY'
        node_y2.label = 'y^2'

        node_xy = group.nodes.new('ShaderNodeMath')
        node_xy.location = (400, -400)
        node_xy.operation = 'MULTIPLY'
        node_xy.label = 'xy'

        # r2,r4,r6,2x2,2y2
        node_r2 = group.nodes.new('ShaderNodeMath')
        node_r2.location = (600, 0)
        node_r2.operation = 'ADD'
        node_r2.label = 'r^2'

        node_r4 = group.nodes.new('ShaderNodeMath')
        node_r4.location = (600, -200)
        node_r4.operation = 'MULTIPLY'
        node_r4.label = 'r^4'

        node_r6 = group.nodes.new('ShaderNodeMath')
        node_r6.location = (600, -400)
        node_r6.operation = 'MULTIPLY'
        node_r6.label = 'r^6'

        node_2x2 = group.nodes.new('ShaderNodeMath')
        node_2x2.location = (600, -600)
        node_2x2.operation = 'MULTIPLY'
        node_2x2.inputs[1].default_value = 2
        node_2x2.label = '2 * x^2'

        node_2y2 = group.nodes.new('ShaderNodeMath')
        node_2y2.location = (600, -800)
        node_2y2.operation = 'MULTIPLY'
        node_2y2.inputs[1].default_value = 2
        node_2y2.label = '2 * y^2'

        # r2m,r4m,r6m
        node_r2m = group.nodes.new('ShaderNodeMath')
        node_r2m.location = (800, 0)
        node_r2m.operation = 'MULTIPLY'
        node_r2m.inputs[1].default_value = 0  # k1
        node_r2m.label = 'k1 * r^2'

        node_r4m = group.nodes.new('ShaderNodeMath')
        node_r4m.location = (800, -200)
        node_r4m.operation = 'MULTIPLY'
        node_r4m.inputs[1].default_value = 0  # k2
        node_r4m.label = 'k2 * r^4'

        node_r6m = group.nodes.new('ShaderNodeMath')
        node_r6m.location = (800, -400)
        node_r6m.operation = 'MULTIPLY'
        node_r6m.inputs[1].default_value = 0  # k3
        node_r6m.label = 'k3 * r^6'

        # r2p,r4p,r6p
        node_r2p = group.nodes.new('ShaderNodeMath')
        node_r2p.location = (1000, 0)
        node_r2p.operation = 'ADD'
        node_r2p.inputs[1].default_value = 1
        node_r2p.label = '1 + k1 * r^2'

        node_r4p = group.nodes.new('ShaderNodeMath')
        node_r4p.location = (1000, -200)
        node_r4p.operation = 'ADD'
        node_r4p.label = '1 + k1 * r^2 + k2 * r^4'

        node_r6p = group.nodes.new('ShaderNodeMath')
        node_r6p.location = (1000, -400)
        node_r6p.operation = 'ADD'
        node_r6p.label = '1 + k1 * r^2 + k2 * r^4 + k3 * r^6'

        # a1,a2,a3
        node_a1 = group.nodes.new('ShaderNodeMath')
        node_a1.location = (1200, 0)
        node_a1.operation = 'MULTIPLY'
        node_a1.inputs[1].default_value = 2
        node_a1.label = '2xy'

        node_a2 = group.nodes.new('ShaderNodeMath')
        node_a2.location = (1200, -200)
        node_a2.operation = 'ADD'
        node_a2.label = 'r^2 + 2x^2'

        node_a3 = group.nodes.new('ShaderNodeMath')
        node_a3.location = (1200, -400)
        node_a3.operation = 'ADD'
        node_a3.label = 'r^2 + 2y^2'

        # a1x,a2x,a3y,a1y
        node_a1x = group.nodes.new('ShaderNodeMath')
        node_a1x.location = (1400, 0)
        node_a1x.operation = 'MULTIPLY'
        node_a1x.inputs[1].default_value = 0  # p1
        node_a1x.label = 'p1 * 2xy'

        node_a2x = group.nodes.new('ShaderNodeMath')
        node_a2x.location = (1400, -200)
        node_a2x.operation = 'MULTIPLY'
        node_a2x.inputs[1].default_value = 0  # p2
        node_a2x.label = 'p2 * (r^2 + 2x^2)'

        node_a1y = group.nodes.new('ShaderNodeMath')
        node_a1y.location = (1400, -400)
        node_a1y.operation = 'MULTIPLY'
        node_a1y.inputs[1].default_value = 0  # p2
        node_a1y.label = 'p2 * 2xy'

        node_a3y = group.nodes.new('ShaderNodeMath')
        node_a3y.location = (1400, -600)
        node_a3y.operation = 'MULTIPLY'
        node_a3y.inputs[1].default_value = 0  # p1
        node_a3y.label = 'p1 * (r^2 + 2y^2)'

        # xd1,xd2,xd3
        node_xd1 = group.nodes.new('ShaderNodeMath')
        node_xd1.location = (1600, 0)
        node_xd1.operation = 'MULTIPLY'
        node_xd1.label = 'x * (1 + k1 * r^2 + k2 * r^4 + k3 * r^6)'

        node_xd2 = group.nodes.new('ShaderNodeMath')
        node_xd2.location = (1600, -200)
        node_xd2.operation = 'ADD'
        node_xd2.label = 'x * (1 + k1 * r^2 + k2 * r^4 + k3 * r^6) + p1 * 2xy'

        node_xd3 = group.nodes.new('ShaderNodeMath')
        node_xd3.location = (1600, -400)
        node_xd3.operation = 'ADD'
        node_xd3.label = 'x * (1 + k1 * r^2 + k2 * r^4 + k3 * r^6) + p1 * 2xy + p2 * (r^2 + 2x^2)'

        # yd1,yd2,yd3
        node_yd1 = group.nodes.new('ShaderNodeMath')
        node_yd1.location = (1800, 0)
        node_yd1.operation = 'MULTIPLY'
        node_yd1.label = 'y * (1 + k1 * r^2 + k2 * r^4 + k3 * r^6)'

        node_yd2 = group.nodes.new('ShaderNodeMath')
        node_yd2.location = (1800, -200)
        node_yd2.operation = 'ADD'
        node_yd2.label = 'y * (1 + k1 * r^2 + k2 * r^4 + k3 * r^6) + p1 * 2xy'

        node_yd3 = group.nodes.new('ShaderNodeMath')
        node_yd3.location = (1800, -400)
        node_yd3.operation = 'ADD'
        node_yd3.label = 'y * (1 + k1 * r^2 + k2 * r^4 + k3 * r^6) + p1 * 2xy + p2 * (r^2 + 2y^2)'

        # combine
        node_combine = group.nodes.new('ShaderNodeCombineXYZ')
        node_combine.location = (2000, 0)
        node_combine.inputs[2].default_value = 1

        node_mapping2 = group.nodes.new('ShaderNodeMapping')
        node_mapping2.location = (2200, 400)
        node_mapping2.inputs['Scale'].default_value[1] = -1  # flip y-axis

        output_node = group.nodes.new("NodeGroupOutput")
        output_node.location = (2200, 0)

        # add links
        # inputs
        group.links.new(input_node.outputs[0], node_mapping1.inputs[0])
        group.links.new(node_mapping1.outputs[0], node_separate.inputs[0])
        group.links.new(input_node.outputs['k1'], node_r2m.inputs[1])
        group.links.new(input_node.outputs['k2'], node_r4m.inputs[1])
        group.links.new(input_node.outputs['k3'], node_r6m.inputs[1])
        group.links.new(input_node.outputs['p1'], node_a1x.inputs[1])
        group.links.new(input_node.outputs['p1'], node_a3y.inputs[1])
        group.links.new(input_node.outputs['p2'], node_a2x.inputs[1])
        group.links.new(input_node.outputs['p2'], node_a1y.inputs[1])

        # x2,y2,xy
        group.links.new(node_separate.outputs[0], node_x2.inputs[0])
        group.links.new(node_separate.outputs[0], node_x2.inputs[1])
        group.links.new(node_separate.outputs[1], node_y2.inputs[0])
        group.links.new(node_separate.outputs[1], node_y2.inputs[1])
        group.links.new(node_separate.outputs[0], node_xy.inputs[0])
        group.links.new(node_separate.outputs[1], node_xy.inputs[1])

        # r2,r4,r6,2x2,2y2
        group.links.new(node_x2.outputs[0], node_r2.inputs[0])
        group.links.new(node_y2.outputs[0], node_r2.inputs[1])
        group.links.new(node_r2.outputs[0], node_r4.inputs[0])
        group.links.new(node_r2.outputs[0], node_r4.inputs[1])
        group.links.new(node_r2.outputs[0], node_r6.inputs[0])
        group.links.new(node_r4.outputs[0], node_r6.inputs[1])
        group.links.new(node_x2.outputs[0], node_2x2.inputs[0])
        group.links.new(node_y2.outputs[0], node_2y2.inputs[0])

        # r2m,r4m,r6m
        group.links.new(node_r2.outputs[0], node_r2m.inputs[0])
        group.links.new(node_r4.outputs[0], node_r4m.inputs[0])
        group.links.new(node_r6.outputs[0], node_r6m.inputs[0])

        # r2p,r4p,r6p
        group.links.new(node_r2m.outputs[0], node_r2p.inputs[0])
        group.links.new(node_r4m.outputs[0], node_r4p.inputs[0])
        group.links.new(node_r2p.outputs[0], node_r4p.inputs[1])
        group.links.new(node_r6m.outputs[0], node_r6p.inputs[0])
        group.links.new(node_r4p.outputs[0], node_r6p.inputs[1])

        # a1,a2,a3
        group.links.new(node_xy.outputs[0], node_a1.inputs[0])
        group.links.new(node_r2.outputs[0], node_a2.inputs[0])
        group.links.new(node_2x2.outputs[0], node_a2.inputs[1])
        group.links.new(node_r2.outputs[0], node_a3.inputs[0])
        group.links.new(node_2y2.outputs[0], node_a3.inputs[1])

        # a1x,a2x,a3y,a1y
        group.links.new(node_a1.outputs[0], node_a1x.inputs[0])
        group.links.new(node_a2.outputs[0], node_a2x.inputs[0])
        group.links.new(node_a3.outputs[0], node_a3y.inputs[0])
        group.links.new(node_a1.outputs[0], node_a1y.inputs[0])

        # xd1,xd2,xd3
        group.links.new(node_separate.outputs[0], node_xd1.inputs[0])
        group.links.new(node_r6p.outputs[0], node_xd1.inputs[1])
        group.links.new(node_xd1.outputs[0], node_xd2.inputs[0])
        group.links.new(node_a1x.outputs[0], node_xd2.inputs[1])
        group.links.new(node_xd2.outputs[0], node_xd3.inputs[0])
        group.links.new(node_a2x.outputs[0], node_xd3.inputs[1])

        # yd1,yd2,yd3
        group.links.new(node_separate.outputs[1], node_yd1.inputs[0])
        group.links.new(node_r6p.outputs[0], node_yd1.inputs[1])
        group.links.new(node_yd1.outputs[0], node_yd2.inputs[0])
        group.links.new(node_a3y.outputs[0], node_yd2.inputs[1])
        group.links.new(node_yd2.outputs[0], node_yd3.inputs[0])
        group.links.new(node_a1y.outputs[0], node_yd3.inputs[1])

        # combine
        group.links.new(node_xd3.outputs[0], node_combine.inputs[0])
        group.links.new(node_yd3.outputs[0], node_combine.inputs[1])

        group.links.new(node_combine.outputs[0], node_mapping2.inputs[0])
        group.links.new(node_mapping2.outputs[0], output_node.inputs[0])

    group.inputs['k1'].default_value = k1
    group.inputs['k2'].default_value = k2
    group.inputs['k3'].default_value = k3
    group.inputs['p1'].default_value = p1
    group.inputs['p2'].default_value = p2
    return group


def set_projector(opencv_matrix: List[List[float]] = None,
                  distortion: List[float] = None,
                  image_path: str = None,
                  pose: List[List[float]] = None,
                  energy: float = 100.0,
                  flip_x: bool = False,
                  flip_y: bool = False,
                  max_bounces: int = 0) -> str:
    if opencv_matrix is None:
        opencv_matrix = [[512, 0, 256], [0, 512, 256], [0, 0, 1]]
    if distortion is None:
        distortion = [0.0, 0.0, 0.0, 0.0, 0.0]
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

    # build node_tree
    node_tree = projector.data.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)

    node_texcoord = node_tree.nodes.new('ShaderNodeTexCoord')
    node_texcoord.location = (-200, 0)

    node_separate = node_tree.nodes.new('ShaderNodeSeparateXYZ')
    node_separate.location = (0, -300)

    node_abs = node_tree.nodes.new('ShaderNodeMath')
    node_abs.location = (0, -150)
    node_abs.operation = 'ABSOLUTE'

    node_divide = node_tree.nodes.new('ShaderNodeVectorMath')
    node_divide.operation = 'DIVIDE'
    node_divide.location = (0, 0)

    k1, k2, k3, p1, p2 = distortion
    distortion_node_group = _new_distortion_node_group(name='ProjectorDistortion', k1=k1, k2=k2, k3=k3, p1=p1, p2=p2)
    node_distortion = node_tree.nodes.new('ShaderNodeGroup')
    node_distortion.node_tree = distortion_node_group
    node_distortion.location = (200, 0)

    node_mapping = node_tree.nodes.new('ShaderNodeMapping')
    node_mapping.location = (400, 0)
    node_mapping.label = 'Mapping - Intrinsics'

    node_mapping2 = node_tree.nodes.new('ShaderNodeMapping')
    node_mapping2.location = (600, 0)
    node_mapping2.label = 'Mapping - Flip'

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
    node_output.location = (1300, -200)

    node_tree.links.new(node_texcoord.outputs[1], node_separate.inputs[0])
    node_tree.links.new(node_texcoord.outputs[1], node_divide.inputs[0])
    node_tree.links.new(node_separate.outputs[2], node_abs.inputs[0])
    node_tree.links.new(node_abs.outputs[0], node_divide.inputs[1])
    node_tree.links.new(node_divide.outputs[0], node_distortion.inputs[0])
    node_tree.links.new(node_distortion.outputs[0], node_mapping.inputs[0])
    node_tree.links.new(node_mapping.outputs[0], node_mapping2.inputs[0])
    node_tree.links.new(node_mapping2.outputs[0], node_teximg.inputs[0])
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
        node_mapping2.inputs['Location'].default_value[0] = 1.0
        node_mapping2.inputs['Scale'].default_value[0] = -1.0
    if flip_y:
        node_mapping2.inputs['Location'].default_value[1] = 1.0
        node_mapping2.inputs['Scale'].default_value[1] = -1.0
    return projector.name


__all__ = ['set_projector']
