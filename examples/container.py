import sys
sys.path.append('.')
import blenderfunc as bf

import bpy
import json
import numpy as np

def remove_invisible_objects():
    bf.render_instance_segmap('/tmp/instance_segmap.png')
    instmap = np.load('/tmp/instance_segmap.npz')['data']
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
    box_obj.name = f'box_{i:04}'
    box_obj.location = pose[:3, 3]
    box_obj.dimensions = dim
    box_obj['class_id'] = 2
 
# set camera
bf.set_camera(pose=[[0.0,  0.0,  1.0,  -6.0],
                    [-1.0, 0.0,  0.0,  0.0],
                    [0.0,  -1.0, 0.0,  0.0],
                    [0.0,  0.0,  0.0,  1.0]],
             image_resolution=(640, 480),
             opencv_matrix=[[320, 0, 320], [0, 240, 240], [0, 0, 1]])

remove_invisible_objects()

bf.render_instance_segmap('output/container/instance_segmap.png')
# bf.render_depth('output/container/depth.png', depth_scale=0.0005)
# bf.render_normal('output/container/normal.png')
# bf.render_class_segmap('output/container/class_segmap.png')
# bf.render_object_masks('output/container/object_masks.png')