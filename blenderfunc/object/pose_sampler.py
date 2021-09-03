import bpy
import math
import numpy as np
from mathutils import Vector, Euler, Matrix
from typing import Callable, List
from blenderfunc.utility.utility import get_object_by_name


def _min_max_sampler(range1: List[float] = None, range2: List[float] = None, range3: List[float] = None):
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
    """Return a random pose sampler that only generates poses above the tote, which ensures the objects will
    fall inside the tote eventually after physics simulation.

    :param tote_name: name of tote
    :param obj_name: name of object
    :param num: number of objects that will be in the tote
    :return: random pose sampler
    :rtype: function
    """
    tote = get_object_by_name(tote_name)
    obj = get_object_by_name(obj_name)
    length, width, height = tote.dimensions
    obj_volume = obj.dimensions[0] * obj.dimensions[1] * obj.dimensions[2]
    pts = np.array([vertex.co for vertex in obj.data.vertices])
    max_dist = np.max(np.linalg.norm(pts, axis=-1))
    x_min = -length / 2 + max_dist
    x_max = length / 2 - max_dist
    y_min = -width / 2 + max_dist
    y_max = width / 2 - max_dist
    if x_min > x_max or y_min > y_max:
        raise Exception('Tote is too small')
    z_min = height + max_dist
    volume = 10 * num * obj_volume
    z_max = z_min + volume / ((x_max - x_min) * (y_max - y_min))

    def sampler():
        pos = _min_max_sampler([x_min, x_max], [y_min, y_max], [z_min, z_max])
        euler = _min_max_sampler([0, 360], [0, 360], [0, 360])
        return pos, euler

    return sampler


def in_view_checker(cam_pose: List[List[float]],
                    cam_intrinsics: List[List[float]],
                    image_resolution: List[int]) -> Callable:
    """Return a checker function to check if all points can be seen in a camera view

    :param cam_pose: 4x4 camera extrinsic matrix
    :type cam_pose: List of Lists
    :param cam_intrinsics: 3x3 camera intrinsic matrix, [[fx,0,cx],[0,fy,cy],[0,0,1]]
    :type cam_intrinsics: List of Lists
    :param image_resolution: [image_width, image_width]
    :type image_resolution: List
    :return: in view checker
    :rtype: function
    """
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


def in_views_sampler(obj_name: str,
                     rand_loc: List[List[float]],
                     rand_rot: List[List[float]],
                     checkers: List[Callable]) -> Callable:
    """Randomly sample poses and check whether an object can be observed completely by multiple cameras

    :param obj_name: name of object to be sampled
    :type obj_name: str
    :param rand_loc: range of random location, [[min_x, max_x], [min_y, max_y], [min_z, max_z]]
    :type rand_loc: List of Lists
    :param rand_rot: range of random euler angle in degree, [[min_r, max_r], [min_p, max_p], [min_y, max_y]]
    :type rand_rot: List of Lists
    :param checkers: checker functions
    :type checkers: List of functions
    """
    obj = get_object_by_name(obj_name)
    pts = [v.co.copy() for v in obj.data.vertices]

    def sampler():
        while True:
            pos = _min_max_sampler(rand_loc[0], rand_loc[1], rand_loc[2])
            angles = _min_max_sampler(rand_rot[0], rand_rot[1], rand_rot[2])
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


__all__ = ['in_tote_sampler', 'in_view_checker', 'in_views_sampler']
