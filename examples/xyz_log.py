import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict", "pyyaml", "opencv-python", "imageio"])

import argparse
import os
import sys
import json
import yaml
import numpy as np
import blenderfunc.all as bf
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


def dump_camera_json(filepath: str, camera_id: str, camera_name: str, intrinsics: List[List[float]],
                     image_resolution: List[float], distort_coeffs: List[float], depth_scale: float):
    data = {
        "camera_id": camera_id,
        "camera_name": camera_name,
        "image_types": ["rgb", "depth", "aligned_depth"],
        "rgb_intr": {
            "fx": intrinsics[0][0],
            "fy": intrinsics[1][1],
            "ppx": intrinsics[0][2],
            "ppy": intrinsics[1][2],
            "width": image_resolution[0],
            "height": image_resolution[1],
            "distortion_model": 4,
            "distortion_coeffs": distort_coeffs
        },
        "depth_intr": {
            "fx": intrinsics[0][0],
            "fy": intrinsics[1][1],
            "ppx": intrinsics[0][2],
            "ppy": intrinsics[1][2],
            "width": image_resolution[0],
            "height": image_resolution[1],
            "distortion_model": 4,
            "distortion_coeffs": distort_coeffs
        },
        "aligned_depth_intr": {
            "fx": intrinsics[0][0],
            "fy": intrinsics[1][1],
            "ppx": intrinsics[0][2],
            "ppy": intrinsics[1][2],
            "width": image_resolution[0],
            "height": image_resolution[1],
            "distortion_model": 4,
            "distortion_coeffs": distort_coeffs
        },
        "depth_scale": depth_scale
    }
    with open(filepath, 'w') as fp:
        json.dump(data, fp, indent=4)


def dump_env_yml(filepath: str, tote_length: float, tote_width: float, tote_height: float, camera_id: str,
                 cam_pose: List[List[float]]):
    data = {
        "totes": {
            "0": {
                "length": tote_length,
                "bottom_length": tote_length,
                "upper_length": tote_length,
                "width": tote_width,
                "bottom_width": tote_width,
                "upper_width": tote_width,
                "height": tote_height,
                "scan_pose": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
                "pose": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
                "sensors": [camera_id]
            }
        },
        "sensors": {
            camera_id: {
                "max_failure_num": -1,
                "near_z": 0.5,
                "far_z": 5.0,
                "capture_timeout_ms": 5000,
                "cfg": "VirtualCamera.json",
                "type": "VirtualCamera",
                "eye_in_hand": "false",
                "pose": cam_pose
            }
        }
    }
    with open(filepath, 'w') as fp:
        yaml.dump(data, fp, sort_keys=False, default_flow_style=None)


def compute_num_pick_sequence(num_begin, num_end, num_pick):
    nums = list(range(num_begin, num_end - 1, -num_pick))
    if nums[-1] > num_end:
        nums.append(num_end)
    nums = [num_begin] + nums
    return np.abs(np.diff(nums)).tolist()


def parse_arguments():
    # ignore arguments before '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, default='output/xyz_log')
    parser.add_argument('--camera_type', type=str, default='XYZ-SL',
                        help='different cameras have different fov and aspect ratio')
    parser.add_argument('--camera_height', type=float, default=2, help='camera height in meter')
    parser.add_argument('--obstruction', type=float, default=0.2,
                        help='control the number of obstructed points, reasonable range [0, 0.4]')
    parser.add_argument('--tote_length', type=float, default=0.7)
    parser.add_argument('--tote_width', type=float, default=0.7)
    parser.add_argument('--tote_height', type=float, default=0.5)
    parser.add_argument('--tote_thickness', type=float, default=0.03)
    parser.add_argument('--model_path', type=str, default='resources/models/brake_disk.ply',
                        help='CAD model, supported format: ply, stl, obj')
    parser.add_argument('--max_faces', type=int, default=10000,
                        help='decimate the mesh if the number of faces of mesh is bigger than this value')
    parser.add_argument('--num_begin', type=int, default=30, help='number of objects in tote at the beginning')
    parser.add_argument('--num_end', type=int, default=0, help='number of objects in tote in the end')
    parser.add_argument('--num_pick', type=int, default=5, help='number of objects picked each time')
    parser.add_argument('--max_bounces', type=int, default=3, help='render option: max bounces of light')
    parser.add_argument('--samples', type=int, default=10, help='render option: samples for each pixel')
    parser.add_argument('--substeps_per_frame', type=int, default=10,
                        help='physics option: steps per frame, higher value for higher simulation stability')
    parser.add_argument('--enable_perfect_depth', action="store_true")
    parser.add_argument('--enable_instance_segmap', action="store_true")
    parser.add_argument('--enable_class_segmap', action="store_true")
    parser.add_argument('--enable_mesh_info', action="store_true")
    args = parser.parse_args(args=argv)

    if args.num_begin < args.num_end:
        raise Exception('num_begin < num_end, please check arguments')
    return args


args = parse_arguments()
camera = camera_infos[args.camera_type]
cam_pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, args.camera_height], [0, 0, 0, 1]]
output_dir = args.output_dir

bf.initialize_folder(output_dir)
bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=camera['intrinsics'], image_resolution=camera['image_resolution'], pose=cam_pose)
light_name = bf.add_light([camera['baseline'], 0, args.camera_height])
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL', class_id=0))
tote = bf.add_tote(length=args.tote_length, width=args.tote_width, height=args.tote_height,
                   thickness=args.tote_thickness,
                   properties=dict(physics=False, collision_shape='MESH', class_id=1))
obj = bf.add_object_from_file(filepath=args.model_path, max_faces=args.max_faces,
                              name=os.path.basename(args.model_path),
                              properties=dict(physics=True, collision_shape='CONVEX_HULL', class_id=2))
bf.export_mesh(filepath=os.path.join(output_dir, 'model.stl'), obj_name=obj)
pose_sampler = bf.in_tote_sampler(tote, obj, args.num_begin)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(args.num_begin - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)

dump_camera_json(filepath=output_dir + '/camera.json', camera_id='BlenderCamera', camera_name='BlenderCamera',
                 intrinsics=camera['intrinsics'], image_resolution=camera['image_resolution'],
                 distort_coeffs=camera['distort_coeffs'], depth_scale=camera['depth_scale'])
dump_env_yml(filepath=output_dir + '/env.yml', tote_length=args.tote_length, tote_width=args.tote_width,
             tote_height=args.tote_height, camera_id='BlenderCamera', cam_pose=cam_pose)

num_pick_seq = compute_num_pick_sequence(args.num_begin, args.num_end, args.num_pick)
for i, num_pick in enumerate(num_pick_seq):
    for _ in range(num_pick):
        bf.remove_highest_object()
    bf.physics_simulation(substeps_per_frame=args.substeps_per_frame)
    timestamp = int(time.time())
    prefix = '{}/{}_{}_'.format(output_dir, timestamp, args.camera_type)
    bf.render_color(prefix + 'rgb.png', denoiser='OPTIX', samples=args.samples, max_bounces=args.max_bounces,
                    save_blend_file=True if i == 0 else False)
    bf.render_depth(prefix + 'aligned_depth.png', depth_scale=camera['depth_scale'], save_npz=False)
    if not args.enable_perfect_depth:
        bf.render_light_mask(prefix + 'light_mask.png', light_name, threshold=args.obstruction)
        bf.apply_nan_mask(prefix + 'aligned_depth.png', prefix + 'light_mask.png', prefix + 'aligned_depth.png')
        os.remove(prefix + 'light_mask.png')
    if args.enable_instance_segmap:
        bf.render_instance_segmap(prefix + 'instance_segmap.png')
    if args.enable_class_segmap:
        bf.render_class_segmap(prefix + 'class_segmap.png')
    if args.enable_mesh_info:
        bf.write_meshes_info(prefix + 'mesh_info.csv')
