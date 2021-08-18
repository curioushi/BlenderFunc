import os
import bpy
from blenderfunc.object.texture import make_smart_uv_project
from blenderfunc.object.collector import get_all_mesh_objects
from blenderfunc.utility.utility import get_object_by_name


def remove_mesh_object(obj_name: str):
    obj = bpy.data.objects.get(obj_name, None)
    if obj:
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj)
        else:
            raise Exception('This object is not a mesh: {}'.format(obj.name))


def add_plane(size: float = 1.0, name: str = 'Plane', properties: dict = None) -> str:
    bpy.ops.mesh.primitive_plane_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_cube(size: float = 2.0, name: str = 'Cube', properties: dict = None) -> str:
    bpy.ops.mesh.primitive_cube_add(size=size)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_ball(radius: float = 1.0, subdivisions=4, name: str = 'Ball', properties: dict = None) -> str:
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
    make_smart_uv_project(obj.name)
    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_ply(filepath: str = None, name: str = 'PlyModel', properties: dict = None) -> str:
    bpy.ops.import_mesh.ply(filepath=filepath)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    make_smart_uv_project(obj.name)
    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_stl(filepath: str = None, name: str = 'STLModel', properties: dict = None) -> str:
    bpy.ops.import_mesh.stl(filepath=filepath)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    make_smart_uv_project(obj.name)
    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_obj(filepath: str = None, name: str = 'OBJModel', properties: dict = None) -> str:
    bpy.ops.import_scene.obj(filepath=filepath)
    objs = bpy.context.selected_objects
    if len(objs) > 1:
        raise Exception("Only support one object in OBJ file: {}".format(objs))
    obj = objs[0]
    obj.name = name
    obj.data.name = name
    if properties is not None:
        for key, value in properties.items():
            obj[key] = value
    return obj.name


def add_object_from_file(filepath: str = None, name: str = "Model", properties: dict = None,
                         max_vertices=float('inf')) -> str:
    ext = os.path.splitext(filepath)[-1]
    if ext == '.ply':
        obj_name = add_ply(filepath, name=name, properties=properties)
    elif ext == '.stl':
        obj_name = add_stl(filepath, name=name, properties=properties)
    elif ext == '.obj':
        obj_name = add_obj(filepath, name=name, properties=properties)
    else:
        raise Exception('Unsupported CAD file format: {}'.format(ext))

    obj = get_object_by_name(obj_name)
    num_vertices_before = len(obj.data.vertices)
    if num_vertices_before > max_vertices:
        ratio = max_vertices / num_vertices_before
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.decimate(ratio=ratio)
        bpy.ops.object.editmode_toggle()
        num_vertices_after = len(obj.data.vertices)
        print('Decimate object: {} -> {}'.format(num_vertices_before, num_vertices_after))

    return obj_name


def duplicate_mesh_object(obj_name: str) -> str:
    obj = get_object_by_name(obj_name)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate(linked=True)
    return bpy.context.active_object.name


def write_meshes_info(filepath: str = '/tmp/temp.csv'):
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
            pose = ' '.join([str(obj.matrix_world[0][0]) for i in range(3) for j in range(4)])
            f.write('{}, {}, {}, {}\n'.format(instance_id, class_id, name, pose))


__all__ = ['add_plane', 'add_cube', 'add_cylinder', 'add_ball', 'add_tote', 'add_ply', 'add_obj', 'add_stl',
           'add_object_from_file', 'remove_mesh_object', 'duplicate_mesh_object', 'write_meshes_info']
