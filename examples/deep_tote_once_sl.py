import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict", "opencv-python"])

import random
import blenderfunc.all as bf
from examples.utility import compute_structured_light_params
from glob import glob

num = 10
cam_K, image_resolution, cam_distort, proj_K, proj_distort, cam2world, proj2world = \
    compute_structured_light_params('resources/sl_param.xml', 2.5)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))

bf.initialize()
hdr_files = list(bf.get_hdr_material_infos().values())
bf.set_hdr_background(random.choice(hdr_files))
bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, distort_coeffs=cam_distort, pose=cam2world)
bf.add_plane(size=3, properties=dict(physics=False, collision_shape='CONVEX_HULL', class_id=1))
tote = bf.add_tote(length=0.7, width=0.9, height=0.7,
                   properties=dict(physics=False, collision_shape='MESH', class_id=2))
obj = bf.add_ply(filepath='resources/models/brake_disk.ply',
                 properties=dict(physics=True, collision_shape='CONVEX_HULL', class_id=3))
pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)
bf.physics_simulation()
mat = bf.add_simple_material(color=[0, 0, 1], metallic=1, roughness=0.3)
bf.set_material(obj, mat)

for i, pattern_path in enumerate(proj_patterns[:1]):
    proj = bf.set_projector(opencv_matrix=proj_K, image_path=pattern_path, distort_coeffs=proj_distort, pose=proj2world)
    bf.render_color('output/deep_tote_once_sl/{:04}.png'.format(i), samples=10, color_mode='RGB', save_blend_file=True)
bf.render_shadow_mask('output/deep_tote_once_sl/shadow_mask.png', proj, save_blend_file=True)
bf.render_depth('output/deep_tote_once_sl/depth.png', save_blend_file=True)
bf.render_instance_segmap('output/deep_tote_once_sl/instance.png', save_blend_file=True)
bf.render_class_segmap('output/deep_tote_once_sl/class.png', save_blend_file=True)
bf.render_normal_map('output/deep_tote_once_sl/normal.png', save_blend_file=True)
bf.write_meshes_info('output/deep_tote_once_sl/info.csv')
