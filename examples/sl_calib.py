import sys
sys.path.append('.')
import blenderfunc as bf
from examples.utility import compute_structured_light_params
from glob import glob

cam_K, image_resolution, cam_distort, proj_K, proj_distort, cam2world, proj2world = \
    compute_structured_light_params('resources/sl_param.xml', cam_height=2)
proj_patterns = sorted(glob('resources/images/sl_calib_patterns/*.bmp'))

bf.initialize()
bf.set_background_light(strength=0)
plane_name = bf.add_plane(size=10)
bf.get_object_by_name(plane_name).location = (0, 0, -1)
board_name = bf.add_object_from_file(filepath='resources/models/calib_board/560x450.obj', name='CalibBoard')
bf.set_camera(opencv_matrix=cam_K, distort_coeffs=cam_distort, image_resolution=image_resolution, pose=cam2world)

# ensure that the calibration board get a good pose
checker1 = bf.in_view_checker(cam_pose=cam2world, cam_intrinsics=cam_K, image_resolution=image_resolution)
checker2 = bf.in_view_checker(cam_pose=proj2world, cam_intrinsics=proj_K, image_resolution=[912, 1140])
pose_sampler = bf.in_views_sampler(board_name,
                                   rand_loc=[[-1, 1], [-1, 1], [0, 0]],
                                   rand_rot=[[60, 120], [-30, 30], [-180, 180]],
                                   checkers=[checker1, checker2])

# HACK: set roughness of calibration board to 1 to prevent reflections
bf.get_object_by_name(board_name).data.materials[0].node_tree.nodes['Principled BSDF'].inputs[ 'Roughness'].default_value = 1.0

for i in range(20):
    bf.get_object_by_name(board_name).matrix_world = pose_sampler()
    for j, pattern_path in enumerate(proj_patterns):
        bf.set_projector(energy=100, opencv_matrix=proj_K, distort_coeffs=proj_distort, pose=proj2world,
                         image_path=pattern_path)
        bf.render_color('output/sl_calib/{:04}/{:04}.png'.format(i, j), samples=10,
                        save_blend_file=True if j == 0 else False)
