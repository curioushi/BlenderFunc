from typing import List
import bpy


def get_all_mesh_objects() -> List[bpy.types.Object]:
    ret = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            ret.append(obj)
    return ret


def get_mesh_objects_by_custom_properties(properties: dict = None) -> List[bpy.types.Object]:
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


__all__ = ['get_all_mesh_objects', 'get_mesh_objects_by_custom_properties']
