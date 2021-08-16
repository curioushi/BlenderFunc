from typing import List

import cv2
import bpy
import numpy as np
from mathutils import Matrix
from blenderfunc.utility.initialize import remove_all_cameras


def set_camera(opencv_matrix: List[List[float]] = None,
               image_resolution: List[int] = None,
               distort_coeffs: List[float] = None,
               pose: List[List[float]] = None,
               clip_start: float = 0.1,
               clip_end: float = 100,
               name: str = 'Camera') -> str:
    if opencv_matrix is None:
        opencv_matrix = [[400, 0, 400], [0, 400, 300], [0, 0, 1]]
    if image_resolution is None:
        image_resolution = [800, 600]
    if distort_coeffs is None:
        distort_coeffs = [0.0, 0.0, 0.0, 0.0, 0.0]  # k1, k2, p1, p2, k3
    if pose is None:
        pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 1], [0, 0, 0, 1]]

    # only one camera in the scene
    remove_all_cameras()

    bpy.ops.object.camera_add()
    cam_ob = bpy.context.active_object
    cam = cam_ob.data
    bpy.context.scene.camera = cam_ob
    cam_ob.name = name
    cam.name = name
    cam.sensor_fit = 'HORIZONTAL'

    fx, fy = opencv_matrix[0][0], opencv_matrix[1][1]
    cx, cy = opencv_matrix[0][2], opencv_matrix[1][2]

    # compute blender attributes
    rx = image_resolution[0]
    ry = image_resolution[1]
    sw = cam.sensor_width
    f = fx * sw / rx
    sh = ry * f / fy
    ax = 1
    ay = (sh / ry) / (sw / rx)
    if ay < 1:
        ax, ay = 1 / ay, 1
    sx = - (((cx + 0.5) / rx) - 0.5)
    sy = (((cy + 0.5) / ry) - 0.5) / (sw / sh)

    # Set focal length
    cam.lens_unit = 'MILLIMETERS'
    cam.lens = f

    # Set resolution
    bpy.context.scene.render.resolution_x = image_resolution[0]
    bpy.context.scene.render.resolution_y = image_resolution[1]

    # Set clipping
    cam.clip_start = clip_start
    cam.clip_end = clip_end

    # Set aspect ratio
    bpy.context.scene.render.pixel_aspect_x = ax
    bpy.context.scene.render.pixel_aspect_y = ay

    # Set shift
    cam.shift_x = sx
    cam.shift_y = sy

    Q = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    blender_pose = np.array(pose).dot(Q)
    cam_ob.matrix_world = Matrix(blender_pose)

    cam_ob['CameraMatrix'] = opencv_matrix
    cam_ob['DistortCoeffs'] = distort_coeffs
    return cam_ob.name


__all__ = ['set_camera']
