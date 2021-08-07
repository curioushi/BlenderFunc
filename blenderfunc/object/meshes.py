from typing import List
import bpy


def remove_mesh(obj: bpy.types.Object):
    if obj.type == 'MESH':
        bpy.data.meshes.remove(obj.data)
    else:
        raise Exception('This object is not a mesh: {}'.format(obj.name))


def add_plane(size: float = 1, name: str = 'Plane', properties: dict = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj


def add_cube(size: float = 2, name: str = 'Cube', properties: dict = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj


__all__ = ['add_plane', 'add_cube', 'remove_mesh']
