from typing import List

import bpy
import numpy as np
from mathutils import Matrix


def set_camera(opencv_matrix: List[List[float]] = None,
               image_resolution: List[int] = None,
               pose: List[List[float]] = None,
               clip_start: float = 0.1,
               clip_end: float = 100):
    if opencv_matrix is None:
        opencv_matrix = [[400, 0, 400], [0, 400, 300], [0, 0, 1]]
    if image_resolution is None:
        image_resolution = [800, 600]
    if pose is None:
        pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]

    # remove all cameras
    for camera in bpy.data.cameras:
        bpy.data.cameras.remove(camera)

    bpy.ops.object.camera_add()
    cam_ob = bpy.data.objects['Camera']
    cam = cam_ob.data
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


__all__ = ['set_camera']
