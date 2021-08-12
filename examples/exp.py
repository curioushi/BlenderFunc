import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict", "imageio"])

import os
import shutil
import numpy as np
import blenderfunc.all as bf
import subprocess
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


cam_K, image_resolution, proj_K, cam2world, proj2world = get_structured_light_params(2.4)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))
num = 35

bf.initialize()
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, pose=cam2world)
bf.add_plane(size=10, properties=dict(physics=False, collision_shape='CONVEX_HULL'))
tote = bf.add_tote(length=0.7, width=0.9, height=0.7, properties=dict(physics=False, collision_shape='MESH'))
obj = bf.add_ply(filepath='resources/models/brake_disk.ply', name='BrakeDisk',
                 properties=dict(physics=True, collision_shape='CONVEX_HULL'))
pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)

bf.physics_simulation(max_simulation_time=10)
bf.render_depth('output/texture_experiment/depth.png')
bf.set_background_light(strength=1)
mat_infos = bf.get_pbr_material_infos()
for i, (mat_name, mat_path) in enumerate(mat_infos.items()):
    bf.remove_all_images()
    bf.remove_all_materials()
    mat = bf.add_pbr_material(mat_path)
    bf.set_material(obj, mat)
    for j, pattern_path in enumerate(proj_patterns):
        bf.set_projector(energy=20, opencv_matrix=proj_K, image_path=pattern_path, pose=proj2world, flip_x=True)
        bf.render_color('output/texture_experiment/{}/{:04}.png'.format(mat_name, j), samples=10)
    subprocess.Popen(['/home/shq/Projects/xyz/xyz-structured-light/build/test/utest_rebuilder',
                      '-i=/home/shq/Projects/mycode/BlenderFunc/output/texture_experiment/{}/'.format(mat_name),
                      '-c=/home/shq/Projects/xyz/xyz-structured-light/build/test/StructuredLight.json']).wait()
    shutil.move('depth_img.png', 'output/texture_experiment/{}/depth.png'.format(mat_name))
    shutil.move('organized_cloud.pcd', 'output/texture_experiment/{}/cloud.pcd'.format(mat_name))
