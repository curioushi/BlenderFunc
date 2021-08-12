from typing import Union, List

import bpy
import numpy as np
from mathutils import Vector, Euler

from blenderfunc.object.meshes import remove_mesh_object
from blenderfunc.object.collector import get_all_mesh_objects, get_mesh_objects_by_custom_properties
from blenderfunc.utility.utility import seconds_to_frames


def enable_rigid_body(obj: bpy.types.Object, physics_type: str = 'PASSIVE',
                      physics_collision_shape: str = 'CONVEX_HULL',
                      physics_collision_margin: float = None):
    bpy.ops.rigidbody.object_add({'object': obj})
    obj.rigid_body.type = physics_type
    obj.rigid_body.collision_shape = physics_collision_shape
    obj.rigid_body.use_margin = True
    obj.rigid_body.collision_margin = physics_collision_margin


def disable_rigid_body(obj: bpy.types.Object):
    bpy.ops.rigidbody.object_remove({'object': obj})


def get_origin(obj: bpy.types.Object) -> Vector:
    return obj.location.copy()


def set_origin(obj: bpy.types.Object, point: Union[list, Vector] = None, mode: str = "POINT") -> Vector:
    context = {"selected_editable_objects": [obj]}

    if mode == "POINT":
        if point is None:
            raise Exception("The parameter point is not given even though the mode is set to POINT.")
        prev_cursor_location = bpy.context.scene.cursor.location
        bpy.context.scene.cursor.location = point
        bpy.ops.object.origin_set(context, type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = prev_cursor_location
    elif mode == "CENTER_OF_MASS":
        bpy.ops.object.origin_set(context, type='ORIGIN_CENTER_OF_MASS')
    elif mode == "CENTER_OF_VOLUME":
        bpy.ops.object.origin_set(context, type='ORIGIN_CENTER_OF_VOLUME')
    else:
        raise Exception("No such mode: " + mode)

    return get_origin(obj)


def persist_transformation_into_mesh(obj: bpy.types.Object, location: bool = True, rotation: bool = True,
                                     scale: bool = True):
    bpy.ops.object.transform_apply({"selected_editable_objects": [obj]}, location=location, rotation=rotation,
                                   scale=scale)


def get_active_objects_pose() -> dict:
    objects_poses = {}
    for obj in get_all_mesh_objects():
        if obj.rigid_body.type == 'ACTIVE':
            location = bpy.context.scene.objects[obj.name].matrix_world.translation.copy()
            rotation = Vector(bpy.context.scene.objects[obj.name].matrix_world.to_euler())
            objects_poses.update({obj.name: {'location': location, 'rotation': rotation}})

    return objects_poses


def simulation(min_simulation_time: float = 5.0, max_simulation_time: float = 10.0, check_object_interval: float = 1.0,
               object_stopped_location_threshold: float = 0.01, object_stopped_rotation_threshold: float = 1.0,
               substeps_per_frame: int = 10, solver_iters: int = 10) -> dict:
    # Shift the origin of all objects to their center of mass to make the simulation more realistic
    origin_shift = {}
    prev_origins = {}

    all_mesh_objects = get_all_mesh_objects()
    for obj in all_mesh_objects:
        prev_origins[obj.name] = get_origin(obj)

    # Select all mesh objects, run origin set
    for obj in bpy.data.objects:
        if obj in all_mesh_objects:
            obj.select_set(True)
        else:
            obj.select_set(False)
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

    for obj in all_mesh_objects:
        new_origin = get_origin(obj)
        origin_shift[obj.name] = new_origin - prev_origins[obj.name]

        # # Persist mesh scaling as having a scale != 1 can make the simulation unstable
        # persist_transformation_into_mesh(obj, location=False, rotation=False, scale=True)

    # Configure simulator
    bpy.context.scene.rigidbody_world.substeps_per_frame = substeps_per_frame
    bpy.context.scene.rigidbody_world.solver_iterations = solver_iters

    # Perform simulation
    bake_physics_simulation(min_simulation_time, max_simulation_time, check_object_interval,
                            object_stopped_location_threshold,
                            object_stopped_rotation_threshold)

    return origin_shift


def have_objects_stopped_moving(last_poses: dict, new_poses: dict, object_stopped_location_threshold: float,
                                object_stopped_rotation_threshold: float) -> bool:
    """ Check if the difference between the two given poses per object is smaller than the configured threshold.
    """
    stopped = True
    for obj_name in last_poses:
        # Check location difference
        location_diff = last_poses[obj_name]['location'] - new_poses[obj_name]['location']
        stopped = stopped and not any(location_diff[i] > object_stopped_location_threshold for i in range(3))

        # Check rotation difference
        rotation_diff = last_poses[obj_name]['rotation'] - new_poses[obj_name]['rotation']
        stopped = stopped and not any(rotation_diff[i] > object_stopped_rotation_threshold for i in range(3))

        if not stopped:
            break

    return stopped


def bake_physics_simulation(min_simulation_time: float, max_simulation_time: float, check_object_interval: float,
                            object_stopped_location_threshold: float, object_stopped_rotation_threshold: float):
    # Run simulation
    point_cache = bpy.context.scene.rigidbody_world.point_cache
    point_cache.frame_start = 1

    if min_simulation_time >= max_simulation_time:
        raise Exception("max_simulation_iterations has to be bigger than min_simulation_iterations")

    # Run simulation starting from min to max in the configured steps
    for current_time in np.arange(min_simulation_time, max_simulation_time, check_object_interval):
        current_frame = seconds_to_frames(current_time)
        print("Running simulation up to " + str(current_time) + " seconds (" + str(current_frame) + " frames)")

        # Simulate current interval
        point_cache.frame_end = current_frame
        bpy.ops.ptcache.bake({"point_cache": point_cache}, bake=True)

        # Go to second last frame and get poses
        bpy.context.scene.frame_set(current_frame - seconds_to_frames(1))
        old_poses = get_active_objects_pose()

        # Go to last frame of simulation and get poses
        bpy.context.scene.frame_set(current_frame)
        new_poses = get_active_objects_pose()

        # If objects have stopped moving between the last two frames, then stop here
        if have_objects_stopped_moving(old_poses, new_poses, object_stopped_location_threshold,
                                       object_stopped_rotation_threshold):
            print("Objects have stopped moving after " + str(current_time) + "  seconds (" + str(
                current_frame) + " frames)")
            break
        elif current_time + check_object_interval >= max_simulation_time:
            print("Stopping simulation as configured max_simulation_time has been reached")
        else:
            # Free bake (this will not completely remove the simulation cache, so further simulations can reuse the already calculated frames)
            bpy.ops.ptcache.free_bake({"point_cache": point_cache})


def physics_simulation(min_simulation_time: float = 1.0, max_simulation_time: float = 10.0):
    # enable rigid body
    for obj in get_all_mesh_objects():
        physics_type = 'ACTIVE' if obj.get('physics', False) else 'PASSIVE'
        physics_collision_shape = obj.get('collision_shape', 'CONVEX_HULL')
        physics_collision_margin = obj.get('collision_margin', 0.0001)
        enable_rigid_body(obj, physics_type, physics_collision_shape, physics_collision_margin)

    bpy.ops.ed.undo_push(message='before simulation')
    obj_poses_before_sim = get_active_objects_pose()
    origin_shifts = simulation(min_simulation_time, max_simulation_time)
    obj_poses_after_sim = get_active_objects_pose()
    bpy.ops.ptcache.free_bake({"point_cache": bpy.context.scene.rigidbody_world.point_cache})
    bpy.ops.ed.undo_push(message='after simulation')
    bpy.ops.ed.undo()

    # Fix the pose of all objects to their pose at the and of the simulation (also revert origin shift)
    objects_with_physics = [obj for obj in get_all_mesh_objects() if obj.rigid_body is not None]
    for obj in objects_with_physics:
        # Skip objects that have parents with compound rigid body component
        if obj.rigid_body.type == "ACTIVE":
            # compute relative object rotation before and after simulation
            R_obj_before_sim = Euler(obj_poses_before_sim[obj.name]['rotation']).to_matrix()
            R_obj_after = Euler(obj_poses_after_sim[obj.name]['rotation']).to_matrix()
            R_obj_rel = R_obj_before_sim @ R_obj_after.transposed()
            # Apply relative rotation to origin shift
            origin_shift = R_obj_rel.transposed() @ origin_shifts[obj.name]
            # Fix pose of object to the one it had at the end of the simulation
            obj.location = obj_poses_after_sim[obj.name]['location'] - origin_shift
            obj.rotation_euler = obj_poses_after_sim[obj.name]['rotation']

    # unset rigid bodys
    for obj in get_all_mesh_objects():
        disable_rigid_body(obj)


def remove_highest_object(mesh_objects: List[bpy.types.Object] = None):
    if mesh_objects is None:
        mesh_objects = get_mesh_objects_by_custom_properties({"physics": True})

    index = -1
    height = -float('inf')
    for i, obj in enumerate(mesh_objects):
        if obj.location[-1] > height:
            height = obj.location[-1]
            index = i
    remove_mesh_object(mesh_objects[index])


__all__ = ['physics_simulation', 'remove_highest_object']
