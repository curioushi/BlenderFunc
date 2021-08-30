import sys
sys.path.append('.')
import blenderfunc as bf

output_dir = 'output/distortion'
cam_K = [[512, 0, 256], [0, 512, 256], [0, 0, 1]]
image_resolution = [512, 512]
cam2world = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 1], [0, 0, 0, 1]]

proj_K = cam_K.copy()
proj_pattern = 'resources/images/test.png'
proj2world = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 1], [0, 0, 0, 1]]

distortions = [[0.3, 0, 0, 0, 0],
               [0, 0.3, 0, 0, 0],
               [0, 0, 0.3, 0, 0],
               [0, 0, 0, 0.3, 0],
               [0, 0, 0, 0, 0.3]]

bf.initialize()
bf.initialize_folder(output_dir, clear_files=True)
bf.add_plane(10)

# no distortion
bf.set_camera(opencv_matrix=cam_K, distort_coeffs=None, image_resolution=image_resolution, pose=cam2world)
bf.set_projector(opencv_matrix=proj_K, distort_coeffs=None, pose=proj2world, image_path=proj_pattern)
bf.render_color('{}/no_distortion.png'.format(output_dir), samples=1, save_blend_file=True)

# only camera distortions
for distortion in distortions:
    bf.set_camera(opencv_matrix=cam_K, distort_coeffs=distortion, image_resolution=image_resolution, pose=cam2world)
    bf.set_projector(opencv_matrix=proj_K, distort_coeffs=None, pose=proj2world, image_path=proj_pattern)
    bf.render_color('{}/cam_{}.png'.format(output_dir, '_'.join([str(x) for x in distortion])), samples=1,
                    save_blend_file=True)

# only projector distortions
for distortion in distortions:
    bf.set_camera(opencv_matrix=cam_K, distort_coeffs=None, image_resolution=image_resolution, pose=cam2world)
    bf.set_projector(opencv_matrix=proj_K, distort_coeffs=distortion, pose=proj2world, image_path=proj_pattern)
    bf.render_color('{}/proj_{}.png'.format(output_dir, '_'.join([str(x) for x in distortion])), samples=1,
                    save_blend_file=True)
