import sys
sys.path.append('.')
import blenderfunc as bf

import bpy
import json
import numpy as np
from pycocotools import mask as cocomask

def remove_invisible_objects(instmap):
    visible_instance_ids = np.unique(instmap) - 1
    invisible_instance_ids = np.setdiff1d(np.arange(len(bf.get_all_mesh_objects())), visible_instance_ids)
    objs = bf.get_all_mesh_objects()
    bpy.ops.object.select_all(action='DESELECT')
    for i in invisible_instance_ids:
        obj = objs[i]
        obj.select_set(True)
    bpy.ops.object.delete()
 
bf.initialize()
bf.initialize_folder('output/container', clear_files=True)
 
# load container
bpy.ops.import_mesh.stl(filepath='resources/container.stl')
container_obj = bpy.context.active_object
container_obj.name = 'a_container'
container_obj['class_id'] = 1
 
# load boxes
boxes_data = json.load(open("resources/boxes.json", "r"))
box_name = bf.add_cube(1)
box_obj = bf.get_object_by_name(box_name)
box_obj.name = 'box'
boxes_obj = [box_obj]
num_boxes = len(boxes_data)
# fast method to create many boxes
while len(boxes_obj) < num_boxes + 1:
    bpy.ops.object.select_all(action='DESELECT')
    num_remain = num_boxes + 1 - len(boxes_obj)
    num_current = len(boxes_obj)
    for i in range(min(num_current, num_remain)):
        boxes_obj[i].select_set(True)
    bpy.ops.object.duplicate()
    boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
bpy.data.objects.remove(box_obj)
# set box pose & dimension
boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
for i, (box_obj, box_data) in enumerate(zip(boxes_obj, boxes_data)):
    pose, dim = np.array(box_data['pose']), box_data['dim']
    box_obj.name = f'box_{i+1:04}'
    box_obj.location = pose[:3, 3]
    box_obj.dimensions = dim
    box_obj['class_id'] = 2
 
# use smaller camera
tf_world_cam = np.array([[0.0,  0.0,  1.0,  -3.0],
                         [-1.0, 0.0,  0.0,  0.0],
                         [0.0,  -1.0, 0.0,  0.0],
                         [0.0,  0.0,  0.0,  1.0]])
bf.set_camera(pose=tf_world_cam,
             image_resolution=(512, 512),
             opencv_matrix=[[256, 0, 256], [0, 256, 256], [0, 0, 1]])

# remove invisible boxes
bf.render_instance_segmap('output/container/box_instmap.png')
box_instmap = np.load('output/container/box_instmap.npz')['data']
remove_invisible_objects(box_instmap)

# rename boxes to make sure the box index == instance id
boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
for i, box_obj in enumerate(boxes_obj):
    box_obj.name = f'box_{i+2:04}' # 0 is background, 1 is container

# use common camera
bf.set_camera(pose=tf_world_cam,
              image_resolution=(1024, 1024),
              opencv_matrix=[[512, 0, 512], [0, 512, 512], [0, 0, 1]])

# render instance boxes again
bf.render_instance_segmap('output/container/box_instmap.png')
instmap = np.load('output/container/box_instmap.npz')['data']
bf.render_object_masks('output/container/box_masks.png', downsample=4)
obj_masks = np.load('output/container/box_masks.npz')['data']

# compute visible ratio
visible_area = np.array([np.sum(instmap == (i + 1)) for i in range(len(obj_masks))])
total_area = np.sum(np.sum(obj_masks, axis=-1), axis=-1)
total_area *= 16  # masks are downsampled by 4
visible_ratio = np.clip(visible_area / total_area, 0, 1)

boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
boxes_data = []
for box_obj in boxes_obj:
    instance_id = int(box_obj.name.split('_')[-1])
    encoded_mask = cocomask.encode(np.asfortranarray(instmap == instance_id))
    encoded_mask['counts'] = encoded_mask['counts'].decode('utf-8')
    tf_world_box = np.array(box_obj.matrix_world.normalized())
    tf_cam_box = np.linalg.inv(tf_world_cam) @ tf_world_box
    boxes_data.append(
        dict(
            instance_id=instance_id,
            pose=tf_cam_box.tolist(),
            dim=np.array(box_obj.dimensions).tolist(),
            mask_box=encoded_mask,
            visible_box=visible_ratio[instance_id - 1]
        )
    )

# # split boxes to 6 planes
# boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
# bpy.ops.object.select_all(action='DESELECT')
# for obj in boxes_obj:
#     obj.select_set(True)
# bpy.context.view_layer.objects.active = boxes_obj[0]
# bpy.ops.object.editmode_toggle()
# bpy.ops.mesh.edge_split(type='EDGE')
# bpy.ops.mesh.separate(type='LOOSE')
# bpy.ops.object.editmode_toggle()

with open('output/container/boxes.json', 'w') as f:
    json.dump(boxes_data, f, indent=4)


# bf.render_instance_segmap('output/container/box_instmap2.png')
# box_instmap2 = np.load('output/container/box_instmap2.npz')['data']


# # plane instance
# bf.render_instance_segmap('output/container/plane_instmap.png')
# plane_instmap = np.load('output/container/plane_instmap.npz')['data']
# remove_invisible_objects(plane_instmap)
# bf.render_instance_segmap('output/container/plane_instmap2.png')
# plane_instmap2 = np.load('output/container/plane_instmap2.npz')['data']


# bf.render_instance_segmap('output/container/box_instance.png')
# 
# 
# remove_invisible_objects()
# 
# bf.render_instance_segmap('output/container/instance_segmap.png')
# bf.render_depth('output/container/depth.png', depth_scale=0.0005)
# bf.render_normal('output/container/normal.png')
# bf.render_class_segmap('output/container/class_segmap.png')
# bf.render_object_masks('output/container/object_masks.png', downsample=4)