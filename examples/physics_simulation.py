import sys
sys.path.append('.')
import blenderfunc as bf

num = 15
model_filepath = 'resources/models/brake_disk.ply'
output_dir = 'output/physics_simulation'
camera_height = 2

bf.initialize()
bf.initialize_folder(output_dir, clear_files=True)
bf.set_background_light(strength=1)
bf.set_camera(pose=[[1,0,0,0], [0,-1,0,0], [0,0,-1,camera_height], [0,0,0,1]])
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL'))
tote = bf.add_tote(length=0.7, width=0.9, height=0.7, properties=dict(physics=False, collision_shape='MESH'))
obj = bf.add_object_from_file(filepath=model_filepath,
                              properties=dict(physics=True, collision_shape='CONVEX_HULL'))

pose_sampler = bf.in_tote_sampler(tote, obj, num)
bf.collision_free_positioning(obj, pose_sampler)
for _ in range(num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_free_positioning(obj, pose_sampler)
bf.save_blend('{}/before_simulation.blend'.format(output_dir))

for i in range(num):
    bf.remove_highest_mesh_object()
    bf.physics_simulation()
    bf.render_color('{}/{:04}.png'.format(output_dir, i), samples=50, denoiser='NLM',
                    save_blend_file=True if i ==0 else False)
