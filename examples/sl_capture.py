import sys
sys.path.append('.')
import blenderfunc as bf
from examples.utility import compute_structured_light_params
from glob import glob


cam_K, image_resolution, cam_distort, proj_K, proj_distort, cam2world, proj2world = \
    compute_structured_light_params('resources/sl_param.xml', 2)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))

bf.initialize()
bf.set_background_light(strength=0)
bf.add_plane(10)
cube_name = bf.add_cube(0.2)
cube = bf.get_object_by_name(cube_name)
cube.location = (0, 0, 0.1)
bf.set_camera(opencv_matrix=cam_K, distort_coeffs=cam_distort, image_resolution=image_resolution, pose=cam2world)
for i, pattern_path in enumerate(proj_patterns):
    bf.set_projector(opencv_matrix=proj_K, distort_coeffs=proj_distort, pose=proj2world, image_path=pattern_path)
    bf.render_color('output/structured_light/{:04}.png'.format(i), samples=1, save_blend_file=True)
