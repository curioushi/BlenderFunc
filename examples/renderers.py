import sys
sys.path.append('.')
import blenderfunc as bf

output_dir = 'output/renderers'

bf.initialize()
bf.initialize_folder(output_dir, clear_files=True)
light_name = bf.add_light(location=[-5, 0, 10], energy=1000)
bf.set_camera(pose=[[1.0,  0.0,  0.0,  0.0],
                    [0.0, -1.0,  0.0,  0.0],
                    [0.0,  0.0, -1.0,  1.0],
                    [0.0,  0.0,  0.0,  1.0]])

bf.add_plane(10, properties={"class_id": 1})

cube_name = bf.add_cube(0.2, properties={"class_id": 2})
bf.get_object_by_name(cube_name).location = (-0.2, -0.2, 0.1)

cube_name = bf.add_cube(0.2, properties={"class_id": 2})
bf.get_object_by_name(cube_name).location = (-0.2, 0.2, 0.1)

ball_name = bf.add_ball(0.1, properties={"class_id": 3})
bf.get_object_by_name(ball_name).location = (0.2, -0.2, 0.1)

ball_name = bf.add_ball(0.1, properties={"class_id": 3})
bf.get_object_by_name(ball_name).location = (0.2, 0.2, 0.1)

bf.render_color('{}/color.png'.format(output_dir), save_blend_file=True, samples=50, denoiser='NLM')
bf.render_depth('{}/depth.png'.format(output_dir), save_blend_file=True, save_npz=True)
bf.render_normal('{}/normal.png'.format(output_dir), save_blend_file=True, save_npz=True)
bf.render_class_segmap('{}/class_segmap.png'.format(output_dir), save_blend_file=True, save_npz=True)
bf.render_instance_segmap('{}/instance_segmap.png'.format(output_dir), save_blend_file=True, save_npz=True)
bf.render_light_mask('{}/light_mask.png'.format(output_dir), light_name=light_name, save_blend_file=True)

