import sys
sys.path.append('.')
import blenderfunc as bf

bf.initialize()
bf.add_light(location=[-5, 0, 10], energy=100)
bf.add_plane(10)
cube_name = bf.add_cube(1)
bf.get_object_by_name(cube_name).location = (0, 0, 0.5)
bf.set_camera(pose=[[1.0,  0.0,  0.0,  0.0],
                    [0.0,  0.0,  1.0, -2.5],
                    [0.0, -1.0,  0.0,  0.5],
                    [0.0,  0.0,  0.0,  1.0]])
bf.render_color('output/helloworld/output.png', save_blend_file=True)
