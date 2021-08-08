from typing import List
import bpy
from blenderfunc.object.collector import get_all_mesh_objects


def physics_simulation(mesh_objects: List[bpy.types.Object] = None):
    if mesh_objects is None:
        mesh_objects = get_all_mesh_objects()

    # set rigid bodys
    for obj in mesh_objects:
        bpy.ops.rigidbody.object_add({'object': obj})
        enable_physics = obj.get('physics', False)
        collision_shape = obj.get('collision_shape', 'CONVEX_HULL')
        obj.rigid_body.type = 'ACTIVE' if enable_physics else 'PASSIVE'
        obj.rigid_body.collision_shape = collision_shape
        # TODO: setting other physics parameters

    # TODO: add physics simulation

    # unset rigid bodys
    for obj in mesh_objects:
        bpy.ops.rigidbody.object_remove({'object': obj})


__all__ = ['physics_simulation']
