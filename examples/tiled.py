import sys

sys.path.append('.')
import blenderfunc as bf
import bpy
import argparse
import os
import sys
import json
import yaml
import math
import numpy as np
import time
from typing import List

camera_infos = {
    "Photoneo-M": {
        "intrinsics": [[2318, 0, 1032], [0, 2318, 772], [0, 0, 1]],
        "image_resolution": [2064, 1544],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.0001,
        "baseline": 0.35
    },
    "Photoneo-L": {
        "intrinsics": [[2345, 0, 1032], [0, 2345, 772], [0, 0, 1]],
        "image_resolution": [2064, 1544],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.0001,
        "baseline": 0.55
    },
    "XYZ-SL": {
        "intrinsics": [[2413, 0, 1024], [0, 2413, 768], [0, 0, 1]],
        "image_resolution": [2048, 1536],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.00005,
        "baseline": 0.25
    }
}


def dump_info_yml(filepath: str, intrinsics: List[List[float]], extrinsics: List[List[float]],
                  image_resolution: List[float], depth_scale: float, distort_coeffs: List[float],
                  tote_length: float, tote_width: float, tote_height: float):
    data = {
        "camera": {
            "intrinsics": intrinsics,
            "extrinsics": extrinsics,
            "image_resolution": image_resolution,
            "depth_scale": depth_scale,
            "distort_coeffs": distort_coeffs
        },
        "tote": {
            "length": tote_length,
            "width": tote_width,
            "height": tote_height
        }
    }
    with open(filepath, 'w') as fp:
        yaml.dump(data, fp, sort_keys=False, default_flow_style=None)


def parse_arguments():
    # ignore arguments before '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, default='output/tiled',
                        help='output directory, the folder will be automatically created if not exist')
    parser.add_argument('--camera_type', type=str, default='XYZ-SL',
                        help='different cameras have different fov and aspect ratio:\n'
                             'Photoneo-M | Photoneo-L | XYZ-SL(default)')
    parser.add_argument('--camera_height', type=float, default=2,
                        help='camera height in meter, default: 2')
    parser.add_argument('--obstruction', type=float, default=0.2,
                        help='control the number of obstructed points, reasonable range 0~0.4, default: 0.2')
    parser.add_argument('--tote_length', type=float, default=0.65, help='tote x-axis dimension, default: 0.7')
    parser.add_argument('--tote_width', type=float, default=0.65, help='tote y-axis dimension, default: 0.7')
    parser.add_argument('--tote_height', type=float, default=1, help='tote z-axis dimension, default: 0.5')
    parser.add_argument('--tote_thickness', type=float, default=0.01, help='tote thickness, default: 0.01')
    parser.add_argument('--model_path', type=str, default='resources/models/brake_disk.ply',
                        help='CAD model, supported format: ply, stl')
    parser.add_argument('--model_max_dimension', type=float, default=0.0,
                        help='rescale the model to this value, if this value <= 0, do nothing')
    parser.add_argument('--max_faces', type=int, default=10000,
                        help='decimate mesh if the number of faces of mesh is bigger than this value, default: 10000')
    parser.add_argument('--x_gap', type=float, default=0.003, help='')
    parser.add_argument('--y_gap', type=float, default=0.003, help='')
    parser.add_argument('--num_begin', type=int, default=0, help='number of objects at the beginning, default: 30')
    parser.add_argument('--num_end', type=int, default=30, help='number of objects in the end, default: 0')
    parser.add_argument('--num_put', type=int, default=5, help='number of objects put each time, default: 5')
    parser.add_argument('--max_bounces', type=int, default=3, help='render option: max bounces of light, default: 3')
    parser.add_argument('--samples', type=int, default=10, help='render option: samples for each pixel, default: 10')
    parser.add_argument('--substeps_per_frame', type=int, default=20,
                        help='physics option: higher value for higher simulation stability, default: 10')
    parser.add_argument('--enable_perfect_depth', action="store_true", help='flag: render depth without obstruction')
    parser.add_argument('--enable_instance_segmap', action="store_true", help='flag: render instance segmentation map')
    parser.add_argument('--enable_object_masks', action="store_true", help='flag: render object masks')
    parser.add_argument('--enable_class_segmap', action="store_true", help='flag: render class segmentation map')
    parser.add_argument('--enable_mesh_info', action="store_true", help='flag: write mesh information including poses')
    args = parser.parse_args(args=argv)
    return args


args = parse_arguments()
camera = camera_infos[args.camera_type]
cam_pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, args.camera_height], [0, 0, 0, 1]]
output_dir = args.output_dir

bf.initialize_folder(output_dir, clear_files=True)
dump_info_yml(filepath=os.path.join(output_dir, 'info.yml'), intrinsics=camera['intrinsics'],
              extrinsics=cam_pose, image_resolution=camera['image_resolution'], depth_scale=camera['depth_scale'],
              distort_coeffs=camera['distort_coeffs'], tote_length=args.tote_length, tote_width=args.tote_width,
              tote_height=args.tote_height)

bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=camera['intrinsics'], image_resolution=camera['image_resolution'], pose=cam_pose)
light_name = bf.add_light([camera['baseline'], 0, args.camera_height])
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL', class_id=0))

# rescale object & export
obj = bf.add_object_from_file(filepath=args.model_path, max_faces=args.max_faces)
if args.model_max_dimension > 0:
    origin_dimensions = bf.get_object_by_name(obj).dimensions
    scale = args.model_max_dimension / max(origin_dimensions)
    bf.get_object_by_name(obj).dimensions = (origin_dimensions[0] * scale,
                                             origin_dimensions[1] * scale,
                                             origin_dimensions[2] * scale)
    bpy.context.view_layer.update()
bf.export_mesh_object(filepath=os.path.join(output_dir, 'model.stl'), obj_name=obj, center_of_mass=True)

# reload object
bf.remove_mesh_object(obj)
obj = bf.add_object_from_file(filepath=os.path.join(output_dir, 'model.stl'), name="Model",
                              properties=dict(physics=True, collision_shape='CONVEX_HULL', class_id=2))

dimensions = bf.get_object_by_name(obj).dimensions

# move first object
bf.get_object_by_name(obj).location = [-args.tote_width / 2 + dimensions[0] / 2,
                                       -args.tote_length / 2 + dimensions[1] / 2,
                                       dimensions[2] / 2]
layer_head_obj = row_head_obj = last_obj = obj
num_cur = 1

image_index = 0
for num_obj in range(args.num_begin, args.num_end + 1, args.num_put):
    if num_obj < num_cur:
        continue
    num_put = num_obj - num_cur
    num_cur = num_obj
    for _ in range(num_put):
        cur_obj = bf.duplicate_mesh_object(last_obj)
        cur_location = bf.get_object_by_name(cur_obj).location
        if cur_location[0] + dimensions[0]/2 + dimensions[0] + args.x_gap < args.tote_width/2:
            bf.get_object_by_name(cur_obj).location[0] += dimensions[0] + args.x_gap
            last_obj = cur_obj
        elif bf.get_object_by_name(row_head_obj).location[1] + dimensions[1]/2 + dimensions[1] + args.y_gap < args.tote_length/2:
            bf.get_object_by_name(cur_obj).location = bf.get_object_by_name(row_head_obj).location
            bf.get_object_by_name(cur_obj).location[1] += dimensions[1] + args.y_gap
            last_obj = cur_obj
            row_head_obj = cur_obj
        else:
            bf.get_object_by_name(cur_obj).location = bf.get_object_by_name(layer_head_obj).location
            bf.get_object_by_name(cur_obj).location[2] += dimensions[2]
            last_obj = cur_obj
            row_head_obj = cur_obj
            layer_head_obj = cur_obj

    # bf.save_blend(os.path.join(output_dir, 'scene_{:04}.blend'.format(image_index)))

    timestamp = int(time.time())
    prefix = '{}/data/{:04}_'.format(output_dir, image_index)
    bf.render_color(prefix + 'color.png', denoiser='OPTIX', samples=args.samples, max_bounces=args.max_bounces, color_mode='BW', save_blend_file=True)
    bf.render_depth(prefix + 'depth.png', depth_scale=camera['depth_scale'], save_npz=False)
    if not args.enable_perfect_depth:
        bf.render_light_mask(prefix + 'lightmask.png', light_name, threshold=args.obstruction)
        bf.apply_binary_mask(prefix + 'depth.png', prefix + 'lightmask.png', prefix + 'depth.png')
        os.remove(prefix + 'lightmask.png')
    if args.enable_instance_segmap:
        bf.render_instance_segmap(prefix + 'instmap.png')
    if args.enable_object_masks:
        bf.render_object_masks(prefix + 'objmasks.png', downsample=4)
    if args.enable_class_segmap:
        bf.render_class_segmap(prefix + 'clsmap.png')
    if args.enable_mesh_info:
        visible_ratio = None
        if args.enable_instance_segmap and args.enable_object_masks:
            inst_segmap = np.load(prefix + 'instmap.npz')['data']
            obj_masks = np.load(prefix + 'objmasks.npz')['data']
            visible_area = np.array([np.sum(inst_segmap == (i + 1)) for i in range(len(obj_masks))])
            total_area = np.sum(np.sum(obj_masks, axis=-1), axis=-1)
            total_area *= 16  # masks are downsampled by 4
            visible_ratio = np.clip(visible_area / total_area, 0, 1)
        bf.export_meshes_info(prefix + 'pose.csv', visible_ratio=visible_ratio)
    image_index += 1
