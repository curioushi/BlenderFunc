import bpy
import sys

sys.path.append('.')

import blenderfunc as bf

bf.setup_custom_packages(["numpy"])
bf.remove_all_data()
bf.set_background_light(strength=1)
cam = bf.set_camera(
    pose=[[1, 0, 0, 0],
          [0, -1, 0, 0],
          [0, 0, -1, 2],
          [0, 0, 0, 1]],
)
bf.add_plane(size=10, name='Ground', properties=dict(physics=False, physics_shape='CONVEX_HULL', class_id=0))
cube = bf.add_cube(size=1, name='Cube', properties=dict(physics=True, physics_shape='CONVEX_HULL', class_id=1))
cube.location = (0, 0, 0.5)
bf.render_color()
bf.render_color()
bf.save_blend()
