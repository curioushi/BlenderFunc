import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict"])

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


cam_K, image_resolution, proj_K, cam2world, proj2world = get_structured_light_params(2.5)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))
num = 50

bf.initialize()
bf.set_background_light(strength=0)
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, pose=cam2world)
bf.add_plane(size=10, properties=dict(physics=False, collision_shape='CONVEX_HULL'))
tote = bf.add_tote(properties=dict(physics=False, collision_shape='MESH'))
obj = bf.add_cylinder(radius=0.05, depth=0.25, properties=dict(physics=True, collision_shape='CONVEX_HULL'))
pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)

for i in range(num):
    bf.remove_highest_object()
    bf.physics_simulation(max_simulation_time=10)
    for j, pattern_path in enumerate(proj_patterns):
        bf.set_projector(opencv_matrix=proj_K, image_path=pattern_path, pose=proj2world, flip_x=True)
        bf.render_color('output/deep_tote_sl/{:04}.png'.format(j + i * len(proj_patterns)), denoiser='OPTIX', samples=10)
        bf.save_blend('output/deep_tote_sl/{:04}.blend'.format(j + i * len(proj_patterns)))
