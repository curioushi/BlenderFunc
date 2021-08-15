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
    proj_distort = sl_param['ProjectorDistCoeffs']
    rot = np.array(sl_param['Rotation'])
    translation = np.array(sl_param['Translation']) / 1000
    cam2proj = np.hstack([rot, translation.reshape(-1, 1)])
    cam2proj = np.vstack([cam2proj, np.array([0, 0, 0, 1])])
    cam2world = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, cam_height], [0, 0, 0, 1]])
    proj2world = cam2world.dot(np.linalg.inv(cam2proj))

    return cam_K, image_resolution, proj_K, proj_distort, cam2world.tolist(), proj2world.tolist()


cam_K, image_resolution, proj_K, proj_distort, cam2world, proj2world = get_structured_light_params(2)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))

bf.initialize()
bf.set_background_light(strength=0)
bf.add_plane(10)
cube_name = bf.add_cube(0.2)
cube = bf.get_object_by_name(cube_name)
cube.location = (0, 0, 0.1)
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, pose=cam2world)
for i, pattern_path in enumerate(proj_patterns):
    bf.set_projector(opencv_matrix=proj_K, distortion=proj_distort, pose=proj2world, image_path=pattern_path,
                     flip_x=True)
    bf.render_color('output/structured_light/{:04}.png'.format(i), samples=1, save_blend_file=True)
