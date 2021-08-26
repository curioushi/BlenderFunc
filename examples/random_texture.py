import sys
sys.path.append('.')
import blenderfunc as bf

bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=[[1200, 0, 500],
                             [0, 1200, 375],
                             [0, 0, 1]],
              image_resolution=[1000, 750],
              pose=[[0.9466491341590881, 0.14329060912132263, -0.28865766525268555, 0.20491363108158112],
                    [0.3222661316394806, -0.420912504196167, 0.8479252457618713, -0.5768105387687683],
                    [9.057018246494408e-08, -0.8957122564315796, -0.44463416934013367, 0.3488265573978424],
                    [0.0, 0.0, 0.0, 1.0]])
bf.add_light(location=[0.32, -0.19, 0.34],
             energy=30)
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL', collision_margin=0.00001))
obj_name = bf.add_object_from_file(filepath='resources/models/brake_disk.ply', uv_project=True,
                                   properties=dict(physics=True, collision_shape='CONVEX_HULL',
                                                   collision_margin=0.00001))
obj = bf.get_object_by_name(obj_name)
obj.location = (0, 0, 0.1)

pbr_infos = bf.get_pbr_material_infos()
for name, path in pbr_infos.items():
    bf.remove_all_materials()
    mat_name = bf.add_pbr_material(path)
    bf.set_material(obj_name, mat_name)
    bf.render_color('output/random_texture/{}.png'.format(name), denoiser='OPTIX', samples=100)
