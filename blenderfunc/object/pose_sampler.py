import bpy
import math
import numpy as np
from mathutils import Vector, Euler, Matrix
from typing import Callable, List
from blenderfunc.object.physics import get_all_mesh_objects
from blenderfunc.utility.utility import get_object_by_name


def _check_no_collision(obj: bpy.types.Object):
    objects_to_check_against = get_all_mesh_objects()

    no_collision = True
    for collision_obj in objects_to_check_against:
        if collision_obj == obj:
            continue
        intersection = _check_bb_intersection(obj, collision_obj)
        if intersection:
            no_collision = False
            break
    return no_collision


def _get_bound_box(obj: bpy.types.Object):
    return [obj.matrix_world @ Vector(cord) for cord in obj.bound_box]


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


def collision_avoidance_positioning(obj_name: str, pose_sampler: Callable, max_trials: int = 100):
    obj = get_object_by_name(obj_name)
    for i in range(max_trials):
        pos, euler = pose_sampler()
        obj.location = pos
        obj.rotation_euler = euler
        bpy.context.view_layer.update()
        no_collision = _check_no_collision(obj)
        if no_collision:
            print('Successfully positioning object in {} trials'.format(i + 1))
            return
    print('Failed to avoid collision when positioning')


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


def in_tote_sampler(tote_name: str, obj_name: str, num: int) -> Callable:
    tote = get_object_by_name(tote_name)
    obj = get_object_by_name(obj_name)
    length, width, height = tote.dimensions
    pts = []
    for vertex in obj.data.vertices:
        pts.append(vertex.co)
    pts = np.array(pts)
    center = np.mean(pts, axis=0)

    max_dist = np.max(np.linalg.norm(pts - center, axis=-1))
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


def in_view_checker(cam_pose: List[List[float]],
                    cam_intrinsics: List[List[float]],
                    image_resolution: List[int]) -> Callable:
    """Return the checker function to check whether points are located in viewport of camera"""
    world2cam = Matrix(cam_pose).copy()
    world2cam.invert()
    cam_K = Matrix(cam_intrinsics)

    def checker(pts: List[Vector]):
        pts_img = [cam_K @ (world2cam @ p) for p in pts]
        pts_img = np.array([(p[0] / p[2], p[1] / p[2]) for p in pts_img], dtype=np.float32)
        min_x = pts_img[:, 0].min()
        max_x = pts_img[:, 0].max()
        min_y = pts_img[:, 1].min()
        max_y = pts_img[:, 1].max()
        return min_x > 0 and max_x < image_resolution[0] and min_y > 0 and max_y < image_resolution[1]

    return checker


def calib_pose_sampler(board_name: str,
                       rand_loc: List[List[float]],
                       rand_rot: List[List[float]],
                       checkers: List[Callable]) -> Callable:
    """ Randomly sample poses and check whether the calibration board can be observed by multiple cameras
    :param board_name: object name of calibration board
    :param rand_loc: [[min_x, max_x], [min_y, max_y], [min_z, max_z]]
    :param rand_rot: [[min_r, max_r], [min_p, max_p], [min_y, max_y]]
    :param checkers: checker functions
    :return:
    """
    board = get_object_by_name(board_name)
    pts = [v.co.copy() for v in board.data.vertices]

    def sampler():
        while True:
            pos = min_max_sampler(rand_loc[0], rand_loc[1], rand_loc[2])
            angles = min_max_sampler(rand_rot[0], rand_rot[1], rand_rot[2])
            angles = [angle / 180 * math.pi for angle in angles]
            euler = Euler(angles)
            rot3x3 = euler.to_matrix()
            matrix_world = Matrix([
                (rot3x3[0][0], rot3x3[0][1], rot3x3[0][2], pos[0]),
                (rot3x3[1][0], rot3x3[1][1], rot3x3[1][2], pos[1]),
                (rot3x3[2][0], rot3x3[2][1], rot3x3[2][2], pos[2]),
                (0, 0, 0, 1)
            ])
            pts_world = [matrix_world @ p for p in pts]
            all_passed = True
            for checker in checkers:
                all_passed = all_passed and checker(pts_world)
                if not all_passed:
                    break
            if all_passed:
                return matrix_world

    return sampler


__all__ = ['collision_avoidance_positioning', 'min_max_sampler', 'in_tote_sampler', 'calib_pose_sampler',
           'in_view_checker']
