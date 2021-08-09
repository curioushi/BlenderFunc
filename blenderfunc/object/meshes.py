from typing import List
import bpy


def remove_mesh(obj: bpy.types.Object):
    if obj.type == 'MESH':
        bpy.data.meshes.remove(obj.data)
    else:
        raise Exception('This object is not a mesh: {}'.format(obj.name))


def add_plane(size: float = 1.0, name: str = 'Plane', properties: dict = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj


def add_cube(size: float = 2.0, name: str = 'Cube', properties: dict = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj


def add_cylinder(radius: float = 0.1, depth: float = 0.3, vertices: int = 64, name: str = 'Cylinder',
                 properties: dict = None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj


def add_tote(length: float = 1.0, width: float = 1.0, height: float = 0.5, thickness: float = 0.02,
             name: str = 'Tote', properties: dict = None) -> bpy.types.Object:
    vertices = [
        # inner points
        (-length / 2, -width / 2, thickness),
        (length / 2, -width / 2, thickness),
        (length / 2, width / 2, thickness),
        (-length / 2, width / 2, thickness),
        (-length / 2, -width / 2, height + thickness),
        (length / 2, -width / 2, height + thickness),
        (length / 2, width / 2, height + thickness),
        (-length / 2, width / 2, height + thickness),
        # outer points
        (-length / 2 - thickness, -width / 2 - thickness, 0),
        (length / 2 + thickness, -width / 2 - thickness, 0),
        (length / 2 + thickness, width / 2 + thickness, 0),
        (-length / 2 - thickness, width / 2 + thickness, 0),
        (-length / 2 - thickness, -width / 2 - thickness, height + thickness),
        (length / 2 + thickness, -width / 2 - thickness, height + thickness),
        (length / 2 + thickness, width / 2 + thickness, height + thickness),
        (-length / 2 - thickness, width / 2 + thickness, height + thickness)]
    faces = [  # inner faces
        (0, 1, 2),
        (2, 3, 0),
        (0, 5, 1),
        (0, 4, 5),
        (1, 6, 2),
        (1, 5, 6),
        (3, 4, 0),
        (3, 7, 4),
        (2, 6, 7),
        (2, 7, 3),
        # outer faces
        (10, 9, 8),
        (8, 11, 10),
        (9, 13, 8),
        (13, 12, 8),
        (10, 14, 9),
        (14, 13, 9),
        (8, 12, 11),
        (12, 15, 11),
        (15, 14, 10),
        (11, 15, 10),
        # upper faces
        (4, 12, 13),
        (4, 13, 5),
        (5, 13, 14),
        (5, 14, 6),
        (6, 14, 15),
        (6, 15, 7),
        (7, 15, 12),
        (7, 12, 4)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj


__all__ = ['add_plane', 'add_cube', 'add_cylinder', 'add_tote', 'remove_mesh']
