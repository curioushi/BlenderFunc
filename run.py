import sys
import numpy as np

sys.path.append('.')

from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow"])

import blenderfunc.all as bf

bf.remove_all_data()
bf.set_background_light(strength=1)
cam = bf.set_camera(
    pose=[[1, 0, 0, 0],
          [0, -1, 0, 0],
          [0, 0, -1, 2],
          [0, 0, 0, 1]],
)
proj = bf.set_projector(
    pose=[[1, 0, 0, 0.1],
          [0, -1, 0, 0],
          [0, 0, -1, 2],
          [0, 0, 0, 1]],
    flip_x=True,
)
bf.add_plane(size=10, name='Ground', properties=dict(physics=False, collision_shape='CONVEX_HULL', class_id=0))
bf.add_tote(properties=dict(physics=False, collision_shape='MESH', class_id=1))
for i in range(50):
    cylinder = bf.add_cylinder(radius=0.05, depth=0.4, name='Cylinder',
                               properties=dict(physics=True, collision_shape='CONVEX_HULL', class_id=2))
    cylinder.location = (1 * np.random.rand() - 0.5, 1 * np.random.rand() - 0.5, np.random.rand() * 10)
for i in range(50):
    bf.remove_highest_object()
    bf.physics_simulation(max_simulation_time=10)
    bf.render_color('/tmp/{}.png'.format(i))
    bf.save_blend('/tmp/{}.blend'.format(i))
