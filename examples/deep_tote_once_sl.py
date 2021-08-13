import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict"])

import bpy
import random
import numpy as np
import blenderfunc.all as bf
from examples.utility import parse_camera_xml
from glob import glob


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


num = 10
cam_K, image_resolution, proj_K, cam2world, proj2world = get_structured_light_params(2.5)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))

bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, pose=cam2world)
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL', class_id=1))
tote = bf.add_tote(length=0.7, width=0.9, height=0.7,
                   properties=dict(physics=False, collision_shape='MESH', class_id=2))
obj = bf.add_ply(filepath='resources/models/brake_disk.ply',
                 properties=dict(physics=True, collision_shape='CONVEX_HULL', class_id=3))
pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)
mat = bf.add_simple_material(color=[1, 0, 0], metallic=1, roughness=0.3)
bf.set_material(obj, mat)

bf.physics_simulation()
for i, pattern_path in enumerate(proj_patterns):
    proj = bf.set_projector(opencv_matrix=proj_K, image_path=pattern_path, pose=proj2world, flip_x=True)
    bf.render_color('output/deep_tote_once_sl/{:04}.png'.format(i), samples=10, color_mode='RGB', save_blend_file=True)
bf.render_shadow_mask('output/deep_tote_once_sl/shadow_mask.png', proj, save_blend_file=True)
bf.render_depth('output/deep_tote_once_sl/depth.png', save_blend_file=True)
bf.render_instance_segmap('output/deep_tote_once_sl/instance.png', save_blend_file=True)
bf.render_class_segmap('output/deep_tote_once_sl/class.png', save_blend_file=True)
bf.render_normal_map('output/deep_tote_once_sl/normal.png', save_blend_file=True)
