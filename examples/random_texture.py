import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict"])

import bpy
import numpy as np
import blenderfunc.all as bf
import random
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


cam_K, image_resolution, _, cam2world, _ = get_structured_light_params(0.7)
num = 1

bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=[[1200, 0, 500],
                             [0, 1200, 375],
                             [0, 0, 1]],
              image_resolution=[1000, 750],
              pose=[[0.9466491341590881, 0.14329060912132263, -0.28865766525268555, 0.20491363108158112],
                    [0.3222661316394806, -0.420912504196167, 0.8479252457618713, -0.5768105387687683],
                    [9.057018246494408e-08, -0.8957122564315796, -0.44463416934013367, 0.3488265573978424],
                    [0.0, 0.0, 0.0, 1.0]])
bf.add_light(location=[0.32, -0.19, 0.34],
             energy=30)
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL', collision_margin=0.00001))
obj_name = bf.add_ply(filepath='resources/models/brake_disk.ply',
                 properties=dict(physics=True, collision_shape='CONVEX_HULL', collision_margin=0.00001))
obj = bf.get_object_by_name(obj_name)
obj.location = (0, 0, 0.1)

pbr_infos = bf.get_pbr_material_infos()
for name, path in pbr_infos.items():
    bf.remove_all_materials()
    mat_name = bf.add_pbr_material(path)
    bf.set_material(obj_name, mat_name)
    bf.render_color('output/random_texture/{}.png'.format(name), denoiser='OPTIX', samples=100)
