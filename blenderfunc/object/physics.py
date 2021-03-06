from typing import Union, Callable

import bpy
import bmesh
import numpy as np
import mathutils
from mathutils import Vector, Euler

from blenderfunc.object.meshes import get_all_mesh_objects, decimate_mesh_object
from blenderfunc.utility.utility import seconds_to_frames, get_object_by_name


def _enable_rigid_body(obj: bpy.types.Object, physics_type: str = 'PASSIVE',
                       physics_collision_shape: str = 'CONVEX_HULL',
                       physics_collision_margin: float = None):
    bpy.ops.rigidbody.object_add({'object': obj})
    obj.rigid_body.type = physics_type
    obj.rigid_body.collision_shape = physics_collision_shape
    obj.rigid_body.use_margin = True
    obj.rigid_body.collision_margin = physics_collision_margin


def _disable_rigid_body(obj: bpy.types.Object):
    bpy.ops.rigidbody.object_remove({'object': obj})


def _get_origin(obj: bpy.types.Object) -> Vector:
    return obj.location.copy()


def _set_origin(obj: bpy.types.Object, point: Union[list, Vector] = None, mode: str = "POINT") -> Vector:
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

    return _get_origin(obj)


def _persist_transformation_into_mesh(obj: bpy.types.Object, location: bool = True, rotation: bool = True,
                                      scale: bool = True):
    bpy.ops.object.transform_apply({"selected_editable_objects": [obj]}, location=location, rotation=rotation,
                                   scale=scale)


def _get_active_objects_pose() -> dict:
    objects_poses = {}
    for obj in get_all_mesh_objects():
        if obj.rigid_body.type == 'ACTIVE':
            location = bpy.context.scene.objects[obj.name].matrix_world.translation.copy()
            rotation = Vector(bpy.context.scene.objects[obj.name].matrix_world.to_euler())
            objects_poses.update({obj.name: {'location': location, 'rotation': rotation}})

    return objects_poses


def _simulation(min_simulation_time: float = 5.0, max_simulation_time: float = 10.0, check_object_interval: float = 1.0,
                object_stopped_location_threshold: float = 0.01, object_stopped_rotation_threshold: float = 1.0,
                substeps_per_frame: int = 10, solver_iters: int = 10) -> dict:
    # Shift the origin of all objects to their center of mass to make the simulation more realistic
    origin_shift = {}
    prev_origins = {}

    all_mesh_objects = get_all_mesh_objects()
    for obj in all_mesh_objects:
        prev_origins[obj.name] = _get_origin(obj)

    # Select all mesh objects, run origin set
    for obj in bpy.data.objects:
        if obj in all_mesh_objects:
            obj.select_set(True)
        else:
            obj.select_set(False)
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

    for obj in all_mesh_objects:
        new_origin = _get_origin(obj)
        origin_shift[obj.name] = new_origin - prev_origins[obj.name]

        # # Persist mesh scaling as having a scale != 1 can make the simulation unstable
        # persist_transformation_into_mesh(obj, location=False, rotation=False, scale=True)

    # Configure simulator
    bpy.context.scene.rigidbody_world.substeps_per_frame = substeps_per_frame
    bpy.context.scene.rigidbody_world.solver_iterations = solver_iters

    # Perform simulation
    _bake_physics_simulation(min_simulation_time, max_simulation_time, check_object_interval,
                             object_stopped_location_threshold,
                             object_stopped_rotation_threshold)

    return origin_shift


def _have_objects_stopped_moving(last_poses: dict, new_poses: dict, object_stopped_location_threshold: float,
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


def _bake_physics_simulation(min_simulation_time: float, max_simulation_time: float, check_object_interval: float,
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
        old_poses = _get_active_objects_pose()

        # Go to last frame of simulation and get poses
        bpy.context.scene.frame_set(current_frame)
        new_poses = _get_active_objects_pose()

        # If objects have stopped moving between the last two frames, then stop here
        if _have_objects_stopped_moving(old_poses, new_poses, object_stopped_location_threshold,
                                        object_stopped_rotation_threshold):
            print("Objects have stopped moving after " + str(current_time) + "  seconds (" + str(
                current_frame) + " frames)")
            break
        elif current_time + check_object_interval >= max_simulation_time:
            print("Stopping simulation as configured max_simulation_time has been reached")
        else:
            # Free bake (this will not completely remove the simulation cache, so further simulations can reuse the already calculated frames)
            bpy.ops.ptcache.free_bake({"point_cache": point_cache})


def physics_simulation(min_simulation_time: float = 1.0, max_simulation_time: float = 10.0,
                       substeps_per_frame: int = 10, max_faces: int = 500):
    """Run physics simulation for a few seconds then freeze the scene. Simulation will stop automatically if the object
    is no longer moving or if the *max_simulation_time* has been reached

    :param min_simulation_time: the simulation will at least run *min_simulation_time* seconds
    :type min_simulation_time: float
    :param max_simulation_time: the simulation will at most run *max_simulation_time* seconds
    :type max_simulation_time: float
    :param substeps_per_frame: number of substeps to solve physics computation per frame, higher value for more stable
        simulation
    :type substeps_per_frame: int
    :param max_faces: reduce the number of faces to speed up collision checking, only works in physics simulation
    :type max_faces: int
    """
    # enable rigid body
    for obj in get_all_mesh_objects():
        physics_type = 'ACTIVE' if obj.get('physics', False) else 'PASSIVE'
        physics_collision_shape = obj.get('collision_shape', 'CONVEX_HULL')
        physics_collision_margin = obj.get('collision_margin', 0.0001)
        _enable_rigid_body(obj, physics_type, physics_collision_shape, physics_collision_margin)

    bpy.ops.ed.undo_push(message='before simulation')
    if max_faces is not None:
        all_mesh_data = set()
        for obj in get_all_mesh_objects():
            if obj.data.name not in all_mesh_data:
                all_mesh_data.add(obj.data.name)
                decimate_mesh_object(obj.name, max_faces)
    obj_poses_before_sim = _get_active_objects_pose()
    origin_shifts = _simulation(min_simulation_time, max_simulation_time, substeps_per_frame=substeps_per_frame)
    obj_poses_after_sim = _get_active_objects_pose()
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
        _disable_rigid_body(obj)


def _check_no_collision(obj: bpy.types.Object, bvh_cache: dict = None):
    objects_to_check_against = get_all_mesh_objects()

    no_collision = True
    for collision_obj in objects_to_check_against:
        if collision_obj == obj:
            continue
        intersection = _check_bb_intersection(obj, collision_obj)
        if intersection:
            intersection, bvh_cache = _check_mesh_intersection(obj, collision_obj, bvh_cache)
        if intersection:
            no_collision = False
            break
    return no_collision, bvh_cache


def _get_bound_box(obj: bpy.types.Object):
    return [obj.matrix_world @ Vector(cord) for cord in obj.bound_box]


def _create_bvh_tree(obj: bpy.types.Object) -> mathutils.bvhtree.BVHTree:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    bm.free()
    return bvh_tree


def _check_mesh_intersection(obj1: bpy.types.Object, obj2: bpy.types.Object, bvh_cache: dict = None):
    if bvh_cache is None:
        bvh_cache = {}

    if len(obj1.data.vertices) == 0 or len(obj2.data.vertices) == 0:
        return False, bvh_cache

    if obj1.name not in bvh_cache:
        obj1_bvhtree = _create_bvh_tree(obj1)
        bvh_cache[obj1.name] = obj1_bvhtree
    else:
        obj1_bvhtree = bvh_cache[obj1.name]

    if obj2.name not in bvh_cache:
        obj2_bvhtree = _create_bvh_tree(obj2)
        bvh_cache[obj2.name] = obj2_bvhtree
    else:
        obj2_bvhtree = bvh_cache[obj2.name]

    inter = len(obj1_bvhtree.overlap(obj2_bvhtree)) > 0
    return inter, bvh_cache


def _check_bb_intersection(obj1: bpy.types.Object, obj2: bpy.types.Object):
    def min_and_max_point(bb):
        values = np.array(bb)
        return np.min(values, axis=0), np.max(values, axis=0)

    bb1 = _get_bound_box(obj1)
    min_b1, max_b1 = min_and_max_point(bb1)
    bb2 = _get_bound_box(obj2)
    min_b2, max_b2 = min_and_max_point(bb2)

    intersection = True
    for min_b1_val, max_b1_val, min_b2_val, max_b2_val in zip(min_b1, max_b1, min_b2, max_b2):
        intersection = intersection and (max_b2_val >= min_b1_val and max_b1_val >= min_b2_val)

    return intersection


def collision_free_positioning(obj_name: str, pose_sampler: Callable, max_trials: int = 100):
    """Placing an object in a collision free position

    :param obj_name: the name of object to be placed
    :type obj_name: str
    :param pose_sampler: a random pose generator
    :type pose_sampler: function
    :param max_trials: max number of trials
    :type max_trials: int
    :return: True if no collision
    :rtype: bool
    """
    bvh_cache = None
    obj = get_object_by_name(obj_name)
    for i in range(max_trials):
        pos, euler = pose_sampler()
        obj.location = pos
        obj.rotation_euler = euler
        if bvh_cache and obj.name in bvh_cache:
            del bvh_cache[obj.name]
        bpy.context.view_layer.update()
        no_collision, bvh_cache = _check_no_collision(obj, bvh_cache)
        if no_collision:
            print('Successfully positioning object in {} trials'.format(i + 1))
            return True
    print('Failed to avoid collision when positioning')
    return False


__all__ = ['physics_simulation', 'collision_free_positioning']
