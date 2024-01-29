import sys
sys.path.append('.')
import blenderfunc as bf

import argparse
import bpy
import os
import os.path as osp
from os.path import join
import math
import json
import numpy as np
from pycocotools import mask as cocomask
from tqdm import tqdm

def remove_invisible_objects(instmap):
    visible_instance_ids = np.unique(instmap) - 1
    invisible_instance_ids = np.setdiff1d(np.arange(len(bf.get_all_mesh_objects())), visible_instance_ids)
    objs = bf.get_all_mesh_objects()
    bpy.ops.object.select_all(action='DESELECT')
    for i in invisible_instance_ids:
        obj = objs[i]
        obj.select_set(True)
    bpy.ops.object.delete()

def plane_statistics(plane_obj):
    verts = np.array([v.co for v in plane_obj.data.vertices])
    dists = np.linalg.norm(verts - verts[0], axis=-1)
    indices = np.argsort(dists)
    i1, i2, i3, i4 = indices[0], indices[1], indices[-1], indices[-2]
    verts = verts[[i1, i2, i3, i4]]
    center = np.mean(verts, axis=0)
    dir_x = verts[3] - verts[0]
    dir_y = verts[1] - verts[0]
    dim_x = np.linalg.norm(dir_x)
    dim_y = np.linalg.norm(dir_y)
    axis_x = dir_x / dim_x
    axis_y = dir_y / dim_y
    axis_z = np.cross(axis_x, axis_y)
    pose = np.eye(4)
    pose[:3, 0] = axis_x
    pose[:3, 1] = axis_y
    pose[:3, 2] = axis_z
    pose[:3, 3] = center
    return pose, [dim_x, dim_y, 0]
 

def generate(container_path, boxes_data_path, output_dir,
             min_fov=120, max_fov=140,
             min_front_dist=0.9, max_front_dist=1.2,
             gap_y=1.0,
             min_height=1.0, max_height=1.3,
             min_yaw=-2, max_yaw=2,
             min_pitch=-7, max_pitch=7):
    bf.initialize_folder(output_dir, clear_files=True)
    bf.initialize()
    # load container
    bpy.ops.import_mesh.stl(filepath=container_path)
    container_obj = bpy.context.active_object
    container_obj.name = 'a_container'
    container_obj['class_id'] = 1
    container_mat = bf.add_simple_material([3/255, 60/255, 120/255], name='container_mat', roughness=1)
    bf.set_material('a_container', container_mat)
    
    # load boxes
    boxes_data = json.load(open(boxes_data_path, "r"))
    box_name = bf.add_cube(1)
    box_mat = bf.add_simple_material([227/255, 157/255, 75/255], name='box_mat', roughness=1)
    bf.set_material(box_name, box_mat)
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
    boxes_min = []
    boxes_max = []
    for i, (box_obj, box_data) in enumerate(zip(boxes_obj, boxes_data)):
        pose, dim = np.array(box_data['pose']), np.array(box_data['dim'])
        box_obj.name = f'BOX_{i+1:04}'
        box_obj.location = pose[:3, 3]
        box_obj.dimensions = dim
        box_obj['class_id'] = 2
        boxes_min.append(pose[:3, 3] - dim / 2)
        boxes_max.append(pose[:3, 3] + dim / 2)
    bbox_min = np.min(boxes_min, axis=0)
    bbox_max = np.max(boxes_max, axis=0)

    random_fov = np.random.uniform(min_fov, max_fov)
    random_dist = np.random.uniform(min_front_dist, max_front_dist)
    random_y = np.random.uniform(bbox_min[1] + gap_y, bbox_max[1] - gap_y)
    random_height = np.random.uniform(min_height, max_height)
    random_yaw = math.radians(np.random.uniform(min_yaw, max_yaw))
    random_pitch = math.radians(np.random.uniform(-min_pitch, max_pitch))

    tf_world_cam = np.array([[0.0,  0.0,  1.0,  bbox_min[0] - random_dist],
                            [-1.0, 0.0,  0.0,  random_y],
                            [0.0,  -1.0, 0.0,  bbox_min[2] + random_height],
                            [0.0,  0.0,  0.0,  1.0]])
    yaw_rot = np.array([[math.cos(random_yaw), -math.sin(random_yaw), 0],
                        [math.sin(random_yaw), math.cos(random_yaw), 0],
                        [0, 0, 1]])
    pitch_rot = np.array([[math.cos(random_pitch), 0, math.sin(random_pitch)],
                        [0, 1, 0],
                        [-math.sin(random_pitch), 0, math.cos(random_pitch)]])
    tf_world_cam[:3, :3] = yaw_rot @ pitch_rot @ tf_world_cam[:3, :3]

    resolution1 = (512, 512)
    resolution2 = (1024, 1024)
    opencv_matrix1 = [[256 / math.tan(math.radians(random_fov/2)), 0, 256],
                    [0, 256 / math.tan(math.radians(random_fov/2)), 256],
                    [0, 0, 1]]
    opencv_matrix2 = [[512 / math.tan(math.radians(random_fov/2)), 0, 512],
                    [0, 512 / math.tan(math.radians(random_fov/2)), 512],
                    [0, 0, 1]]

    # use smaller camera
    bf.set_camera(pose=tf_world_cam,
                image_resolution=resolution1,
                opencv_matrix=opencv_matrix1)

    # remove invisible boxes
    bf.render_instance_segmap('/tmp/box_instmap.png')
    box_instmap = np.load('/tmp/box_instmap.npz')['data']
    remove_invisible_objects(box_instmap)

    # rename boxes to make sure the box index == instance id
    boxes_obj = [obj for obj in bpy.data.objects if 'BOX' in obj.name]
    for i, box_obj in enumerate(boxes_obj):
        box_obj.name = f'box_{i+2:04}' # 0 is background, 1 is container

    # use common camera
    bf.set_camera(pose=tf_world_cam,
                image_resolution=resolution2,
                opencv_matrix=opencv_matrix2)

    # render instance boxes again
    bf.render_instance_segmap(join(output_dir, f'box_instmap.png'))
    instmap = np.load(join(output_dir, f'box_instmap.npz'))['data']
    bf.render_object_masks(join(output_dir, f'box_masks.png'), downsample=4)
    obj_masks = np.load(join(output_dir, f'box_masks.npz'))['data']
    os.remove(join(output_dir, f'box_masks.png'))
    os.remove(join(output_dir, f'box_masks.npz'))

    # compute visible ratio
    visible_area = np.array([np.sum(instmap == (i + 1)) for i in range(len(obj_masks))])
    total_area = np.sum(np.sum(obj_masks, axis=-1), axis=-1)
    total_area *= 16  # masks are downsampled by 4
    visible_ratio = np.clip(visible_area / total_area, 0, 1)

    boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
    output_json = dict()
    for box_obj in boxes_obj:
        instance_id = int(box_obj.name.split('_')[-1])
        binary_mask = np.asfortranarray(instmap == instance_id)
        encoded_mask = cocomask.encode(binary_mask)
        encoded_mask['counts'] = encoded_mask['counts'].decode('utf-8')
        encoded_mask['area'] = int(binary_mask.sum())
        encoded_mask['visible'] = visible_ratio[instance_id - 1]
        tf_world_box = np.array(box_obj.matrix_world.normalized())
        tf_cam_box = np.linalg.inv(tf_world_cam) @ tf_world_box
        output_json[instance_id] = dict(
            pose_box=tf_cam_box.tolist(),
            dim_box=np.array(box_obj.dimensions).tolist(),
            mask_box=encoded_mask,
        )

    # split boxes to 6 planes
    boxes_obj = [obj for obj in bpy.data.objects if 'box' in obj.name]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in boxes_obj:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = boxes_obj[0]
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_split(type='EDGE')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # remove invisible planes
    bf.set_camera(pose=tf_world_cam,
                image_resolution=resolution1,
                opencv_matrix=opencv_matrix1)

    bf.render_instance_segmap(join(output_dir, f'plane_instmap.png'))
    plane_instmap = np.load(join(output_dir, f'plane_instmap.npz'))['data']
    remove_invisible_objects(plane_instmap)

    bf.set_camera(pose=tf_world_cam,
                image_resolution=resolution2,
                opencv_matrix=opencv_matrix2)
    bf.render_instance_segmap(join(output_dir, f'plane_instmap.png'))
    instmap = np.load(join(output_dir, f'plane_instmap.npz'))['data']
    bf.render_object_masks(join(output_dir, f'plane_masks.png'), downsample=4)
    obj_masks = np.load(join(output_dir, f'plane_masks.npz'))['data']
    os.remove(join(output_dir, f'plane_masks.png'))
    os.remove(join(output_dir, f'plane_masks.npz'))

    # compute visible ratio
    visible_area = np.array([np.sum(instmap == (i + 1)) for i in range(len(obj_masks))])
    total_area = np.sum(np.sum(obj_masks, axis=-1), axis=-1)
    total_area *= 16  # masks are downsampled by 4
    visible_ratio = np.clip(visible_area / total_area, 0, 1)

    plane_objs = [obj for obj in bpy.data.objects if 'box' in obj.name]
    for i, plane_obj in tqdm(enumerate(plane_objs)):
        pose_plane, dim_plane = plane_statistics(plane_obj)
        plane_instance_id = i + 2
        box_instance_id = int(plane_obj.name.split('_')[-1].split('.')[0])
        try:
            plane_index = int(plane_obj.name.split('_')[-1].split('.')[1])
        except:
            plane_index = 0
        binary_mask = np.asfortranarray(instmap == plane_instance_id)
        encoded_mask = cocomask.encode(binary_mask)
        encoded_mask['counts'] = encoded_mask['counts'].decode('utf-8')
        encoded_mask['area'] = int(binary_mask.sum())
        encoded_mask['visible'] = visible_ratio[plane_instance_id - 1]
        tf_cam_plane = np.linalg.inv(tf_world_cam) @ pose_plane
        output_json[box_instance_id].update(
            {
                f"mask_plane_{plane_index}": encoded_mask,
                f"pose_plane_{plane_index}": tf_cam_plane.tolist(),
                f"dim_plane_{plane_index}": dim_plane
            }
        )

    bf.render_depth(join(output_dir, f'depth.png'), depth_scale=0.0001)
    bf.render_normal(join(output_dir, f'normal.png'))
    bf.set_background_light([1,1,1], 5)
    bf.render_color(join(output_dir, f'color.png'), denoiser='OPTIX', samples=64)

    with open(join(output_dir, f'boxes.json'), 'w') as f:
        json.dump(output_json, f, indent=4)

def parse_arguments():
    # ignore arguments before '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, default='output/container/0000')
    parser.add_argument('--container_path', type=str, default='resources/Container1K/container_0000.stl')
    parser.add_argument('--boxes_data_path', type=str, default='resources/Container1K/boxes_0000.json')
    parser.add_argument('--random_seed', type=int, default=0)
    args = parser.parse_args(args=argv)
    return args

args = parse_arguments()
np.random.seed(args.random_seed)
generate(container_path=args.container_path,
         boxes_data_path=args.boxes_data_path,
         output_dir=args.output_dir)