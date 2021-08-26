import bpy
import os
import math
from glob import glob
from typing import List
from blenderfunc.utility.utility import get_material_by_name, get_object_by_name


def get_hdr_material_infos(hdr_root: str = 'resources/hdr') -> dict:
    """Get the information of HDR materials, we use free textures from polyhaven.com

    :param hdr_root: root directory of downloaded textures
    :return: textures information
    :rtype: dict, key=texture_name, value=texture_filepath
    """
    if not os.path.exists(hdr_root):
        raise Exception('Please run python3 scripts/download_hdr.py first to download hdr textures')
    hdr_files = list(glob(hdr_root + '/*.hdr'))
    hdr_names = [os.path.basename(f) for f in hdr_files]
    return dict(zip(hdr_names, hdr_files))


def set_hdr_background(filepath: str,
                       rot_x: float = 0.0, rot_y: float = 0.0, rot_z: float = 0.0,
                       scale_x: float = 1.0, scale_y: float = 1.0, scale_z: float = 1.0):
    """Set background light to specified HDR texture

    :param filepath: hdr texture filepath
    :param rot_x: texture mapping x-axis rotation in degree
    :type rot_y: float
    :param rot_y: texture mapping y-axis rotation in degree
    :type rot_y: float
    :param rot_z: texture mapping z-axis rotation in degree
    :type rot_z: float
    :param scale_x: texture mapping x-axis scale
    :type scale_x: float
    :param scale_y: texture mapping y-axis scale
    :type scale_y: float
    :param scale_z: texture mapping z-axis scale
    :type scale_z: float
    """
    for world in bpy.data.worlds:
        bpy.data.worlds.remove(world)
    bpy.ops.world.new()
    world = bpy.data.worlds['World']
    bpy.data.scenes['Scene'].world = world

    world.use_nodes = True
    tree = world.node_tree
    nodes = tree.nodes
    links = tree.links

    for node in nodes:
        nodes.remove(node)

    n_coord = nodes.new('ShaderNodeTexCoord')
    n_coord.location = (0, 0)
    n_mapping = nodes.new('ShaderNodeMapping')
    n_mapping.location = (200, 0)
    n_mapping.inputs['Rotation'].default_value[0] = rot_x / 180 * math.pi
    n_mapping.inputs['Rotation'].default_value[1] = rot_y / 180 * math.pi
    n_mapping.inputs['Rotation'].default_value[2] = rot_z / 180 * math.pi
    n_mapping.inputs['Scale'].default_value[0] = scale_x
    n_mapping.inputs['Scale'].default_value[1] = scale_y
    n_mapping.inputs['Scale'].default_value[2] = scale_z
    n_tex = nodes.new('ShaderNodeTexEnvironment')
    n_tex.location = (400, 0)
    n_output = nodes.new('ShaderNodeOutputWorld')
    n_output.location = (700, 0)

    links.new(n_coord.outputs[0], n_mapping.inputs[0])
    links.new(n_mapping.outputs[0], n_tex.inputs[0])
    links.new(n_tex.outputs[0], n_output.inputs[0])
    image = load_image(filepath)
    n_tex.image = image


def get_pbr_material_infos(texture_root: str = 'resources/cctextures') -> dict:
    """Get the information of PBR materials, we use free textures from cc0textures.com

    :param texture_root: root directory of downloaded textures. each texture with a folder, in the folder
        there are multiple texture images
    :return: textures information
    :rtype: dict, key=texture_name, value=texture_folder
    """
    if not os.path.exists(texture_root):
        raise Exception('Please run python3 scripts/download_textures.py first to download textures')
    texture_folders = sorted(list(glob(texture_root + '/*')))
    texture_folders = [path for path in texture_folders if os.path.isdir(path)]  # only directories

    # only valid folders
    valid_folders = []
    for texture_folder in texture_folders:
        texture_types = [name.split('.')[-2].split('_')[-1] for name in list(glob(texture_folder + '/*.jpg'))]
        if 'Color' in texture_types:
            valid_folders.append(texture_folder)

    texture_names = [os.path.basename(path) for path in valid_folders]
    texture_info = dict(zip(texture_names, valid_folders))
    return texture_info


def load_image(path) -> bpy.types.Image:
    """Load an image to Blender environment, the name of loaded image will be set to its basename

    :param path: path to the image to be loaded
    :return: blender image object
    :rtype: bpy.types.Image
    """
    loaded_img = bpy.data.images.get(os.path.basename(path), None)
    if loaded_img:
        return loaded_img
    return bpy.data.images.load(os.path.abspath(path))


def set_material(obj_name: str, mat_name: str):
    """Set the material to the object

    :param obj_name: object name
    :type obj_name: str
    :param mat_name: material name
    :type mat_name: str
    """
    obj = get_object_by_name(obj_name)
    mat = get_material_by_name(mat_name)
    if obj.type != 'MESH':
        raise Exception('Only mesh can set material')
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def add_simple_material(color: List[float] = None, metallic: float = 0.0, roughness: float = 0.5,
                        name: str = "Material") -> str:
    """Add a simple uniform material

    :param color: rgb value, black=[0,0,0], white=[1,1,1]
    :type color: List
    :param metallic: control the metallic of material, valid range: [0,1]
    :type metallic: float
    :param roughness: control the roughness of material, valid range: [0,1]
    :type roughness: float
    :param name: material_name
    :type name: str
    :return:  material_name
    :rtype: str
    """
    if color is None:
        color = (0.8, 0.8, 0.8, 1)
    elif len(color) == 3:
        color.append(1)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    for node in tree.nodes:
        tree.nodes.remove(node)
    n_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    n_output = nodes.new('ShaderNodeOutputMaterial')
    links.new(n_bsdf.outputs['BSDF'], n_output.inputs['Surface'])

    n_bsdf.inputs['Base Color'].default_value = color
    n_bsdf.inputs['Metallic'].default_value = metallic
    n_bsdf.inputs['Roughness'].default_value = roughness

    return mat.name


def add_pbr_material(texture_folder: str, name: str = "Material",
                     loc_x: float = 0.0, loc_y: float = 0.0, rot_z: float = 0.0,
                     scale_x: float = 1.0, scale_y: float = 1.0) -> str:
    """Add a PBR texture from a texture folder

    :param texture_folder: the texture folder contains multiple texture images
    :type texture_folder: str
    :param name: texture_name
    :type name: str
    :param loc_x: texture mapping x-axis offset
    :type loc_x: float
    :param loc_y: texture mapping y-axis offset
    :type loc_y: float
    :param rot_z: texture mapping z-axis rotation in degree
    :type rot_z: float
    :param scale_x: texture mapping x-axis scale
    :type scale_x: float
    :param scale_y: texture mapping y-axis scale
    :type scale_y: float
    :return: texture_name
    :rtype: str
    """
    texture_paths = list(glob(texture_folder + '/*.jpg'))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    for node in tree.nodes:
        tree.nodes.remove(node)

    # create nodes
    n_tex_coord = nodes.new('ShaderNodeTexCoord')
    n_mapping = nodes.new("ShaderNodeMapping")
    n_ao_tex = nodes.new('ShaderNodeTexImage')
    n_color_tex = nodes.new('ShaderNodeTexImage')
    n_metal_tex = nodes.new('ShaderNodeTexImage')
    n_rgh_tex = nodes.new('ShaderNodeTexImage')
    n_nrm_tex = nodes.new('ShaderNodeTexImage')
    n_disp_tex = nodes.new('ShaderNodeTexImage')
    n_rgbmix = nodes.new("ShaderNodeMixRGB")
    n_output = nodes.new('ShaderNodeOutputMaterial')
    n_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    n_invert = nodes.new("ShaderNodeInvert")
    n_sep_rgb = nodes.new('ShaderNodeSeparateRGB')
    n_comb_rgb = nodes.new('ShaderNodeCombineRGB')
    n_normal_map = nodes.new('ShaderNodeNormalMap')
    n_disp = nodes.new('ShaderNodeDisplacement')

    # set location
    n_tex_coord.location = (0, 0)
    n_mapping.location = (200, 0)
    n_ao_tex.location = (400, 600)
    n_color_tex.location = (400, 300)
    n_metal_tex.location = (400, 0)
    n_rgh_tex.location = (400, -300)
    n_nrm_tex.location = (400, -600)
    n_disp_tex.location = (400, -900)
    n_rgbmix.location = (700, 500)
    n_sep_rgb.location = (700, -600)
    n_invert.location = (900, -700)
    n_comb_rgb.location = (1100, -600)
    n_normal_map.location = (1300, -600)
    n_disp.location = (700, -900)
    n_bsdf.location = (1500, 0)
    n_output.location = (1800, -600)

    # set links
    links.new(n_tex_coord.outputs['UV'], n_mapping.inputs['Vector'])
    links.new(n_mapping.outputs['Vector'], n_ao_tex.inputs['Vector'])
    links.new(n_mapping.outputs['Vector'], n_color_tex.inputs['Vector'])
    links.new(n_mapping.outputs['Vector'], n_metal_tex.inputs['Vector'])
    links.new(n_mapping.outputs['Vector'], n_rgh_tex.inputs['Vector'])
    links.new(n_mapping.outputs['Vector'], n_nrm_tex.inputs['Vector'])
    links.new(n_mapping.outputs['Vector'], n_disp_tex.inputs['Vector'])
    links.new(n_bsdf.outputs['BSDF'], n_output.inputs['Surface'])

    ao_tex_path = [path for path in texture_paths if 'AmbientOcclusion.jpg' in path]
    color_tex_path = [path for path in texture_paths if 'Color.jpg' in path]
    metal_tex_path = [path for path in texture_paths if 'Metalness.jpg' in path]
    rgh_tex_path = [path for path in texture_paths if 'Roughness.jpg' in path]
    normal_tex_path = [path for path in texture_paths if 'Normal.jpg' in path]
    disp_tex_path = [path for path in texture_paths if 'Displacement.jpg' in path]

    if ao_tex_path:
        n_ao_tex.image = load_image(ao_tex_path[0])
        n_ao_tex.image.colorspace_settings.name = 'sRGB'

    if color_tex_path:
        n_color_tex.image = load_image(color_tex_path[0])
        n_color_tex.image.colorspace_settings.name = 'sRGB'
        if ao_tex_path:
            links.new(n_ao_tex.outputs['Color'], n_rgbmix.inputs['Color1'])
            links.new(n_color_tex.outputs['Color'], n_rgbmix.inputs['Color2'])
            n_rgbmix.blend_type = 'MULTIPLY'
            links.new(n_rgbmix.outputs['Color'], n_bsdf.inputs['Base Color'])
        else:
            links.new(n_color_tex.outputs['Color'], n_bsdf.inputs['Base Color'])

    if metal_tex_path:
        n_metal_tex.image = load_image(metal_tex_path[0])
        n_metal_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(n_metal_tex.outputs['Color'], n_bsdf.inputs['Metallic'])

    if rgh_tex_path:
        n_rgh_tex.image = load_image(rgh_tex_path[0])
        n_rgh_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(n_rgh_tex.outputs['Color'], n_bsdf.inputs['Roughness'])

    if normal_tex_path:
        n_nrm_tex.image = load_image(normal_tex_path[0])
        n_nrm_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(n_nrm_tex.outputs['Color'], n_sep_rgb.inputs['Image'])
        links.new(n_sep_rgb.outputs['R'], n_comb_rgb.inputs['R'])
        links.new(n_sep_rgb.outputs['G'], n_invert.inputs['Color'])
        links.new(n_invert.outputs['Color'], n_comb_rgb.inputs['G'])
        links.new(n_sep_rgb.outputs['B'], n_comb_rgb.inputs['B'])
        links.new(n_comb_rgb.outputs['Image'], n_normal_map.inputs['Color'])
        links.new(n_normal_map.outputs['Normal'], n_bsdf.inputs['Normal'])

    if disp_tex_path:
        n_disp_tex.image = load_image(disp_tex_path[0])
        n_disp_tex.image.colorspace_settings.name = 'Non-Color'
        links.new(n_disp_tex.outputs['Color'], n_disp.inputs['Height'])
        n_disp.inputs['Scale'].default_value = 0.002
        links.new(n_disp.outputs['Displacement'], n_output.inputs['Displacement'])

    n_mapping.inputs['Location'].default_value[0] = loc_x
    n_mapping.inputs['Location'].default_value[1] = loc_y
    n_mapping.inputs['Rotation'].default_value[2] = rot_z / 180 * math.pi
    n_mapping.inputs['Scale'].default_value[0] = scale_x
    n_mapping.inputs['Scale'].default_value[1] = scale_y

    return mat.name


__all__ = ['get_pbr_material_infos', 'add_pbr_material', 'add_simple_material', 'load_image', 'set_material',
           'get_hdr_material_infos', 'set_hdr_background']
