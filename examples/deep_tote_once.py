import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict"])

import blenderfunc.all as bf
from examples.utility import compute_structured_light_params

cam_K, image_resolution, _, _, _, cam2world, _ = \
    compute_structured_light_params('resources/sl_param.xml', 2)
num = 35

bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, pose=cam2world)
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL'))
tote = bf.add_tote(length=0.7, width=0.9, height=0.7, properties=dict(physics=False, collision_shape='MESH'))
obj = bf.add_object_from_file(filepath='resources/models/brake_disk.ply',
                              properties=dict(physics=True, collision_shape='CONVEX_HULL'))
pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)

bf.physics_simulation()
bf.render_color('output/deep_tote_once/output.png', save_blend_file=True)
