import sys
sys.path.append('.')
import blenderfunc as bf

cam_K = [[512, 0, 256], [0, 512, 256], [0, 0, 1]]
image_resolution = [512, 512]
cam_distort = [0,0,0,0,0]
cam_pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 2], [0, 0, 0, 1]]
output_dir = 'output/calibration'

bf.initialize()
bf.initialize_folder(output_dir, clear_files=True)
bf.set_background_light(color=[1,1,1], strength=1)
plane_name = bf.add_plane(size=10)
board_name = bf.add_object_from_file(filepath='resources/models/calib_board/560x450.obj', name='CalibBoard')
bf.set_camera(opencv_matrix=cam_K, distort_coeffs=cam_distort, image_resolution=image_resolution, pose=cam_pose)

# ensure that the calibration board get a good pose
checker1 = bf.in_view_checker(cam_pose=cam_pose, cam_intrinsics=cam_K, image_resolution=image_resolution)
pose_sampler = bf.in_views_sampler(board_name,
                                   rand_loc=[[-1, 1], [-1, 1], [0.5, 0.5]],
                                   rand_rot=[[60, 120], [-30, 30], [-180, 180]],
                                   checkers=[checker1])

# HACK: set roughness of calibration board to 1 to prevent reflections
bf.get_object_by_name(board_name).data.materials[0].node_tree.nodes['Principled BSDF'].inputs[ 'Roughness'].default_value = 1.0

for i in range(20):
    bf.get_object_by_name(board_name).matrix_world = pose_sampler()
    bf.render_color('{}/{:04}.png'.format(output_dir, i), samples=32, denoiser='NLM', save_blend_file=True)
