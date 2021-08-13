from typing import List

import bpy


def initialize():
    remove_all_data()
    bpy.context.preferences.filepaths.texture_directory = ''
    bpy.context.preferences.filepaths.render_output_directory = ''


def remove_all_data():
    """remove all data except the default scene"""
    for collection in dir(bpy.data):
        data_structure = getattr(bpy.data, collection)
        if isinstance(data_structure, bpy.types.bpy_prop_collection) and hasattr(data_structure, "remove"):
            for block in data_structure:
                if not isinstance(block, bpy.types.Scene) or block.name != "Scene":
                    data_structure.remove(block)


def remove_all_images():
    """remove all images"""
    for img in bpy.data.images:
        bpy.data.images.remove(img)


def remove_all_materials():
    """remove all materials"""
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)


def remove_all_meshes():
    """remove all mesh objects"""
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)


def remove_all_cameras():
    """remove all camera objects"""
    for cam in bpy.data.cameras:
        bpy.data.cameras.remove(cam)


def remove_all_lights():
    """remove all camera objects"""
    for light in bpy.data.lights:
        bpy.data.lights.remove(light)


def set_background_light(color: List[float] = None, strength: float = 1.0) -> str:
    """set background lighting"""
    for world in bpy.data.worlds:
        bpy.data.worlds.remove(world)
    bpy.ops.world.new()
    world = bpy.data.worlds['World']
    bpy.data.scenes['Scene'].world = world

    if color is None:
        color = [0.05, 0.05, 0.05, 1]
    elif len(color) == 3:
        color.append(1)
    world.node_tree.nodes['Background'].inputs['Color'].default_value = color
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = strength
    return world.name


__all__ = ['remove_all_data', 'remove_all_cameras', 'remove_all_meshes', 'remove_all_materials', 'remove_all_images',
           'set_background_light', 'initialize']
