import bpy
import numpy as np
from mathutils import Vector
from typing import Callable, List
from blenderfunc.object.physics import get_all_mesh_objects


def collision_avoidance_positioning(obj: bpy.types.Object, pose_sampler: Callable, max_trials: int = 100):
    for i in range(max_trials):
        pos, euler = pose_sampler()
        obj.location = pos
        obj.rotation_euler = euler
        bpy.context.view_layer.update()
        no_collision = check_no_collision(obj)
        if no_collision:
            print('Successfully positioning object in {} trials'.format(i + 1))
            return
    print('Failed to avoid collision when positioning')


def check_no_collision(obj: bpy.types.Object):
    objects_to_check_against = get_all_mesh_objects()

    no_collision = True
    for collision_obj in objects_to_check_against:
        if collision_obj == obj:
            continue
        intersection = check_bb_intersection(obj, collision_obj)
        if intersection:
            no_collision = False
            break
    return no_collision


def get_bound_box(obj: bpy.types.Object):
    return [obj.matrix_world @ Vector(cord) for cord in obj.bound_box]


def check_bb_intersection(obj1: bpy.types.Object, obj2: bpy.types.Object):
    def min_and_max_point(bb):
        values = np.array(bb)
        return np.min(values, axis=0), np.max(values, axis=0)

    bb1 = get_bound_box(obj1)
    min_b1, max_b1 = min_and_max_point(bb1)
    bb2 = get_bound_box(obj2)
    min_b2, max_b2 = min_and_max_point(bb2)

    intersection = True
    for min_b1_val, max_b1_val, min_b2_val, max_b2_val in zip(min_b1, max_b1, min_b2, max_b2):
        intersection = intersection and (max_b2_val >= min_b1_val and max_b1_val >= min_b2_val)

    return intersection


def min_max_sampler(range1: List[float] = None, range2: List[float] = None, range3: List[float] = None):
    if range1 is None:
        range1 = [0, 0]
    if range2 is None:
        range2 = [0, 0]
    if range3 is None:
        range3 = [0, 0]
    ret = (np.random.rand() * (range1[1] - range1[0]) + range1[0],
           np.random.rand() * (range2[1] - range2[0]) + range2[0],
           np.random.rand() * (range3[1] - range3[0]) + range3[0])
    return ret


def in_tote_sampler(tote: bpy.types.Object, obj: bpy.types.Object, num: int):
    length, width, height = tote.dimensions
    pts = []
    for vertex in obj.data.vertices:
        pts.append(vertex.co)
    pts = np.array(pts)

    max_dist = np.max(np.linalg.norm(pts, axis=-1))
    x_min = - length / 2 + max_dist
    x_max = length / 2 - max_dist
    y_min = -width / 2 + max_dist
    y_max = width / 2 - max_dist
    if x_min > x_max or y_min > y_max:
        raise Exception('Tote is too small')
    z_min = height + max_dist
    volume = 2 * num * ((2 * max_dist) ** 3)
    z_max = z_min + volume / ((x_max - x_min) * (y_max - y_min))

    def sampler():
        pos = min_max_sampler([x_min, x_max], [y_min, y_max], [z_min, z_max])
        euler = min_max_sampler([0, 360], [0, 360], [0, 360])
        return pos, euler

    return sampler


__all__ = ['collision_avoidance_positioning', 'min_max_sampler', 'in_tote_sampler']
