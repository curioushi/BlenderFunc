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
bf.add_plane(size=10, name='Ground', properties=dict(physics=False, collision_shape='CONVEX_HULL', class_id=0))
cube = bf.add_cube(size=1, name='Cube', properties=dict(physics=True, collision_shape='CONVEX_HULL', class_id=1))
cube.location = (0, 0, 2)
bf.physics_simulation()
bf.render_color('/tmp/{}.png'.format(strength))
bf.save_blend('/tmp/{}.blend'.format(strength))
