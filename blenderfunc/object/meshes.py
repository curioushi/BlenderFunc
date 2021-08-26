import os
import bpy
import bmesh
from typing import List
from blenderfunc.utility.utility import get_object_by_name


def _make_smart_uv_project(obj_name: str):
    obj = get_object_by_name(obj_name)
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


def remove_mesh_object(obj_name: str):
    """Remove the mesh object by its name"""
    obj = bpy.data.objects.get(obj_name, None)
    if obj:
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj)
        else:
            raise Exception('This object is not a mesh: {}'.format(obj.name))


def remove_highest_mesh_object(mesh_objects: List[bpy.types.Object] = None):
    """Remove the highest mesh object in the scene

    :param mesh_objects: the highest object in these objects will be removed, if this value is None, all objects with
        custom properties "physics = True" will be selected
    :type mesh_objects: List of bpy.types.Object
    """
    if mesh_objects is None:
        mesh_objects = get_mesh_objects_by_custom_properties({"physics": True})

    index = -1
    height = -float('inf')
    for i, obj in enumerate(mesh_objects):
        if obj.location[-1] > height:
            height = obj.location[-1]
            index = i
    remove_mesh_object(mesh_objects[index].name)


def add_plane(size: float = 1.0, name: str = 'Plane', properties: dict = None) -> str:
    """Add a plane to the scene"""
    bpy.ops.mesh.primitive_plane_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_cube(size: float = 2.0, name: str = 'Cube', properties: dict = None) -> str:
    """Add a cube to the scene"""
    bpy.ops.mesh.primitive_cube_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_ball(radius: float = 1.0, subdivisions=4, name: str = 'Ball', properties: dict = None) -> str:
    """Add a ball to the scene"""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_cylinder(radius: float = 0.1, depth: float = 0.3, vertices: int = 64, name: str = 'Cylinder',
                 properties: dict = None) -> str:
    """Add a cylinder to the scene"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_tote(length: float = 1.0, width: float = 1.0, height: float = 0.5, thickness: float = 0.02,
             name: str = 'Tote', properties: dict = None) -> str:
    """Add a tote to the scene"""
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
    _make_smart_uv_project(obj.name)
    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def _add_ply(filepath: str = None) -> bpy.types.Object:
    bpy.ops.import_mesh.ply(filepath=filepath)
    obj = bpy.context.active_object
    return obj


def _add_stl(filepath: str = None) -> bpy.types.Object:
    bpy.ops.import_mesh.stl(filepath=filepath)
    obj = bpy.context.active_object
    return obj


def _add_obj(filepath: str = None) -> bpy.types.Object:
    bpy.ops.import_scene.obj(filepath=filepath)
    objs = bpy.context.selected_objects
    if len(objs) > 1:
        raise Exception("Only support one object in OBJ file: {}".format(objs))
    obj = objs[0]
    return obj


def decimate_mesh_object(obj_name: str, max_faces: int = 10000):
    """Decimate the mesh object to target number of faces

    :param obj_name: the name of object to be decimated
    :type obj_name: str
    :param max_faces: the number of faces of mesh object will be decimate to this value
    :type max_faces: int
    """
    obj = get_object_by_name(obj_name)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = bmesh.from_edit_mesh(obj.data)
    num_faces_before = len(mesh.faces)
    if num_faces_before > max_faces:
        ratio = max_faces / num_faces_before
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.decimate(ratio=ratio)
        num_faces_after = len(mesh.faces)
        print('Decimate object "{}": {} -> {}'.format(obj_name, num_faces_before, num_faces_after))
    bpy.ops.object.mode_set(mode='OBJECT')


def add_object_from_file(filepath: str = None, name: str = "Model", max_faces: int = None,
                         uv_project: bool = False, properties: dict = None) -> str:
    """Add an object from model file

    :param filepath: model file path, supported format: ply | stl | obj
    :type filepath: str
    :param name: object_name
    :type name: str
    :param max_faces: decimate the model if the number of faces larger than this value. if this value is None, do nothing
    :type max_faces: int
    :param uv_project: automatically generate the uv map of this object
    :type uv_project: bool
    :param properties: custom properties for physics simulation, useful properties:

        - physics(bool) -- if true, the object will be moved in physics simulation, otherwise, only do collision check

        - collision_shape(str) -- collision shape in physics simulation, options: "MESH" or "CONVEX_HULL"

        - class_id(int) -- class id in ``render_class_segmap``

    :type properties: dict
    :return: object_name
    :rtype: str
    """
    ext = os.path.splitext(filepath)[-1]
    if ext == '.ply':
        obj = _add_ply(filepath)
    elif ext == '.stl':
        obj = _add_stl(filepath)
    elif ext == '.obj':
        obj = _add_obj(filepath)
    else:
        raise Exception('Unsupported CAD file format: {}'.format(ext))

    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value

    if uv_project:
        _make_smart_uv_project(obj.name)

    if max_faces is not None:
        decimate_mesh_object(obj.name, max_faces)

    return obj.name


def duplicate_mesh_object(obj_name: str) -> str:
    """Duplicate the mesh object by its name, use this function instead of loop to add new object to save memory

    :param obj_name: the name of object to be duplicated
    :type obj_name: str
    :return: object_name of new object
    :rtype: str
    """
    obj = get_object_by_name(obj_name)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate(linked=True)
    return bpy.context.active_object.name


def export_mesh_object(filepath: str, obj_name: str, center_of_mass: bool = False):
    """Export the mesh object to a specified filepath

    :param filepath: output filepath, supported file format: ply | stl
    :type filepath: str
    :param obj_name: name of object to be exported
    :type obj_name: str
    :param center_of_mass: if true, reset the origin of object to its center of mass
    :type center_of_mass: bool
    """
    ext = os.path.splitext(filepath)[-1]
    if ext not in ['.ply', '.stl']:
        raise Exception('export_mesh only support ply and stl format')
    bpy.ops.ed.undo_push(message='before export_mesh()')
    for obj in bpy.data.objects:
        if obj.name != obj_name:
            bpy.data.objects.remove(obj)
    obj = bpy.data.objects[0]
    if center_of_mass:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    if ext == '.ply':
        bpy.ops.export_mesh.ply(filepath=filepath)
    elif ext == '.stl':
        bpy.ops.export_mesh.stl(filepath=filepath)
    print('Export CAD Model: {}'.format(filepath))
    bpy.ops.ed.undo_push(message='after export_mesh()')
    bpy.ops.ed.undo()


def separate_isolated_meshes(obj_name: str) -> List[str]:
    """Separate a mesh into multiple meshes if they have no linked parts

    :param obj_name: name of object to be separated
    :type obj_name: str
    :return: list of separated object names
    :rtype: List of str
    """
    obj = get_object_by_name(obj_name)
    objects_before_separate = set([obj.name for obj in get_all_mesh_objects()])
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    objects_after_separate = set([obj.name for obj in get_all_mesh_objects()])
    ret_names = list(objects_after_separate - objects_before_separate)
    ret_names.append(obj_name)
    print('Separate model: {} -> {}'.format(obj_name, ret_names))
    return ret_names


def export_meshes_info(filepath: str = '/tmp/temp.csv'):
    """Export information of all objects in the scene to a csv file, an example of csv file:

    instance_id(int), class_id(int), name(str), pose(flattened 3x4 matrix)

    1, 1, Plane, 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0

    ...

    :param filepath: output filepath
    """
    if os.path.splitext(filepath)[-1] not in ['.csv']:
        raise Exception('Unsupported file format: {}'.format(os.path.splitext(filepath)[-1]))

    output_dir = os.path.abspath(os.path.dirname(filepath))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    mesh_objects = get_all_mesh_objects()
    with open(filepath, 'w') as f:
        f.write('instance_id, class_id, name, pose\n')
        for i, obj in enumerate(mesh_objects):
            instance_id = i + 1
            class_id = obj.get('class_id', 0)
            name = obj.name
            pose = ' '.join([str(obj.matrix_world[i][j]) for i in range(3) for j in range(4)])
            f.write('{}, {}, {}, {}\n'.format(instance_id, class_id, name, pose))


def get_all_mesh_objects() -> List[bpy.types.Object]:
    """Get all mesh objects in the scene

    :return: list of blender objects
    :rtype: List of bpy.types.Object
    """
    ret = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            ret.append(obj)
    return ret


def get_mesh_objects_by_custom_properties(properties: dict = None) -> List[bpy.types.Object]:
    """Get mesh objects have the specified custom properties

    :param properties: object custom properties
    :type properties: dict
    :return: list of blender objects
    :rtype: List of bpy.types.Object
    """
    if properties is None:
        properties = []

    all_objects_set = set(get_all_mesh_objects())
    not_matched_objects_set = set()

    for obj in get_all_mesh_objects():
        for key, value in properties.items():
            obj_value = obj.get(key, None)
            if obj_value != value:
                not_matched_objects_set.add(obj)

    return list(all_objects_set - not_matched_objects_set)


__all__ = ['add_plane', 'add_cube', 'add_cylinder', 'add_ball', 'add_tote', 'add_object_from_file',
           'decimate_mesh_object', 'remove_mesh_object', 'remove_highest_mesh_object', 'duplicate_mesh_object',
           'separate_isolated_meshes', 'export_meshes_info', 'export_mesh_object', 'get_all_mesh_objects',
           'get_mesh_objects_by_custom_properties']
