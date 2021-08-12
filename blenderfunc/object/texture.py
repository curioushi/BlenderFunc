import bpy
import os
from glob import glob


def get_pbr_material_infos(texture_root: str = 'resources/cctextures') -> dict:
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
    loaded_img = bpy.data.images.get(os.path.basename(path), None)
    if loaded_img:
        return loaded_img
    return bpy.data.images.load(os.path.abspath(path))


def set_material(obj: bpy.types.Object, mat: bpy.types.Material):
    if obj.type != 'MESH':
        raise Exception('Only mesh can set material')
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def add_pbr_material(texture_folder: str, name: str = "Material") -> bpy.types.Material:
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

    return mat


def make_smart_uv_project(obj: bpy.types.Object):
    if obj.type == 'MESH':
        prev_active = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.editmode_toggle()  # entering edit mode
        bpy.ops.mesh.select_all(action='SELECT')  # select all objects elements
        bpy.ops.uv.smart_project()  # the actual unwrapping operation
        bpy.ops.object.editmode_toggle()  # exiting edit mode
        bpy.context.view_layer.objects.active = prev_active
    else:
        raise Exception("only MESH object can be smart uv project")


__all__ = ['get_pbr_material_infos', 'add_pbr_material', 'load_image', 'set_material', 'make_smart_uv_project']
