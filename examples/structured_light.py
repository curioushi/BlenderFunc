import sys
sys.path.append('.')
import blenderfunc as bf
from examples.utility import compute_structured_light_params
from glob import glob

cam_K = [[512, 0, 256],
         [0, 512, 256],
         [0,   0,   1]]
image_resolution = [512, 512]
cam_distort = [0, 0, 0, 0, 0]
cam_pose = [[1, 0, 0, 0],
            [0,-1, 0, 0],
            [0, 0,-1, 2],
            [0, 0, 0, 1]]

proj_K = [[1024, 0, 456],
          [0, 1024, 570],
          [0,   0,   1]]
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))
proj_distort = [0, 0, 0, 0, 0]
proj_pose = [[1, 0, 0, 0.2],
             [0,-1, 0, 0],
             [0, 0,-1, 2],
             [0, 0, 0, 1]]
output_dir = 'output/structured_light'

bf.initialize()
bf.initialize_folder(output_dir, clear_files=True)
bf.add_plane(10)
cube_name = bf.add_cube(0.2)
cube = bf.get_object_by_name(cube_name)
cube.location = (0, 0, 0.1)
bf.set_camera(opencv_matrix=cam_K, distort_coeffs=cam_distort, image_resolution=image_resolution, pose=cam_pose)
for i, pattern_path in enumerate(proj_patterns):
    bf.set_projector(opencv_matrix=proj_K, distort_coeffs=proj_distort, pose=proj_pose, image_path=pattern_path)
    bf.render_color('{}/{:04}.png'.format(output_dir, i), samples=32, save_blend_file=True)
