import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict"])

import numpy as np
import blenderfunc.all as bf
from examples.utility import parse_camera_xml


def get_structured_light_params(cam_height=1.5):
    sl_param = parse_camera_xml('resources/sl_param.xml')

    cam_K = sl_param['CameraIntrinsics']
    image_resolution = sl_param['ImageSize']
    proj_K = sl_param['ProjectorIntrinsics']
    rot = np.array(sl_param['Rotation'])
    translation = np.array(sl_param['Translation']) / 1000
    cam2proj = np.hstack([rot, translation.reshape(-1, 1)])
    cam2proj = np.vstack([cam2proj, np.array([0, 0, 0, 1])])
    cam2world = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, cam_height], [0, 0, 0, 1]])
    proj2world = cam2world.dot(np.linalg.inv(cam2proj))

    return cam_K, image_resolution, proj_K, cam2world.tolist(), proj2world.tolist()


cam_K, image_resolution, _, cam2world, _ = get_structured_light_params(2.5)
num = 35

bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, pose=cam2world)
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL'))
tote = bf.add_tote(length=0.7, width=0.9, height=0.7, properties=dict(physics=False, collision_shape='MESH'))
obj = bf.add_ply(filepath='resources/models/brake_disk.ply', properties=dict(physics=True, collision_shape='CONVEX_HULL'))
pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)

bf.physics_simulation()
bf.render_color('output/deep_tote_once/output.png')
bf.save_blend('output/deep_tote_once/output.blend')
