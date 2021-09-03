import os
import bpy
import shutil
from glob import glob


def initialize():
    """Initialize Blender environments:

        1. remove all data in the default scene
        2. use absolute paths
    """
    remove_all_data()
    bpy.context.preferences.filepaths.texture_directory = ''
    bpy.context.preferences.filepaths.render_output_directory = ''


def remove_all_data():
    """Remove all data except the default scene"""
    for collection in dir(bpy.data):
        data_structure = getattr(bpy.data, collection)
        if isinstance(data_structure, bpy.types.bpy_prop_collection) and hasattr(data_structure, "remove"):
            for block in data_structure:
                if not isinstance(block, bpy.types.Scene) or block.name != "Scene":
                    data_structure.remove(block)


def remove_all_images():
    """Remove all images"""
    for img in bpy.data.images:
        bpy.data.images.remove(img)


def remove_all_materials():
    """Remove all materials"""
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)


def remove_all_meshes():
    """Remove all mesh objects"""
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)


def remove_all_cameras():
    """Remove all camera objects"""
    for cam in bpy.data.cameras:
        bpy.data.cameras.remove(cam)


def remove_all_lights():
    """Remove all camera objects"""
    for light in bpy.data.lights:
        bpy.data.lights.remove(light)


def initialize_folder(directory: str, clear_files: bool = False):
    """Make a folder if it does not exist

    :param directory: The path to the directory will be initialized
    :type directory: str
    :param clear_files: Remove all files and directories in the folders
    :type clear_files: bool, optional
    """
    if clear_files:
        shutil.rmtree(directory, ignore_errors=True)
    os.makedirs(directory, exist_ok=True)


def save_blend(filepath: str = '/tmp/temp.blend'):
    """Save ".blend" file to filepath, the output directory will be created """
    output_dir = os.path.dirname(filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(filepath):
        os.remove(filepath)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, relative_remap=False)


def seconds_to_frames(seconds: float) -> int:
    """Convert seconds to frames """
    return int(seconds * bpy.context.scene.render.fps)


def frames_to_seconds(frames: int) -> float:
    """Convert frames to seconds"""
    return float(frames) / bpy.context.scene.render.fps


def get_object_by_name(name: str) -> bpy.types.Object:
    """Get the blender object by its name """
    obj = bpy.data.objects.get(name, None)
    if obj:
        return obj
    else:
        raise Exception('Object "{}" does not exist'.format(name))


def get_material_by_name(name: str) -> bpy.types.Material:
    """Get the blender material by its name """
    obj = bpy.data.materials.get(name, None)
    if obj:
        return obj
    else:
        raise Exception('Material "{}" does not exist'.format(name))


__all__ = ['remove_all_data', 'remove_all_cameras', 'remove_all_meshes', 'remove_all_materials', 'remove_all_images',
           'remove_all_lights', 'initialize', 'initialize_folder', 'save_blend', 'seconds_to_frames',
           'frames_to_seconds', 'get_material_by_name', 'get_object_by_name']
