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

camera_infos = {
    "Photoneo-M": {
        "intrinsics": [[2318, 0, 1032], [0, 2318, 772], [0, 0, 1]],
        "image_resolution": [2064, 1544],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.0001
    },
    "Photoneo-L": {
        "intrinsics": [[2345, 0, 1032], [0, 2345, 772], [0, 0, 1]],
        "image_resolution": [2064, 1544],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.0001
    },
    "XYZ-SL": {
        "intrinsics": [[2413, 0, 1024], [0, 2413, 768], [0, 0, 1]],
        "image_resolution": [2048, 1536],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.00005
    },
    "Tuyang-801": {
        "intrinsics": [[1085, 0, 640], [0, 1085, 480], [0, 0, 1]],
        "image_resolution": [1280, 960],
        "distort_coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "depth_scale": 0.001
    }
}


def dump_camera_json(filepath, camera_id, camera_name, intrinsics, image_resolution, distort_coeffs, depth_scale):
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


def dump_env_yml(filepath, tote_length, tote_width, tote_height, camera_id, cam_pose):
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


def parse_arguments():
    # ignore arguments before '--'
    argv = sys.argv[sys.argv.index('--') + 1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, default='output/xyz_log')
    parser.add_argument('--camera_type', type=str, default='XYZ-SL',
                        help='different cameras have different fov and aspect ratio')
    parser.add_argument('--height', type=float, default=2, help='camera height')
    parser.add_argument('--proj_x', type=float, default=0.1, help='projector x offset')
    parser.add_argument('--tote_length', type=float, default=1)
    parser.add_argument('--tote_width', type=float, default=1)
    parser.add_argument('--tote_height', type=float, default=0.5)
    parser.add_argument('--tote_thickness', type=float, default=0.03)
    parser.add_argument('--num', type=int, default=10, help='number of objects in tote')
    parser.add_argument('--object_path', type=str, default='', help='CAD model, supported format: ply')
    parser.add_argument('--max_bounces', type=int, default=3, help='render option: max bounces of light')
    parser.add_argument('--samples', type=int, default=10, help='render option: samples for each pixel')
    parser.add_argument('--substeps_per_frame', type=int, default=10,
                        help='physics option: steps per frame, higher value for higher simulation stability')
    parser.add_argument('--nan_threshold', type=float, default=0.2,
                        help='this threshold control the area of nan points, reasonable range [0, 0.4]')
    args = parser.parse_args(args=argv)
    return args


args = parse_arguments()
camera = camera_infos[args.camera_type]
cam_pose = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, args.height], [0, 0, 0, 1]]
output_dir = args.output_dir

bf.initialize_folder(output_dir)
bf.initialize()
bf.set_background_light(strength=1)
bf.set_camera(opencv_matrix=camera['intrinsics'], image_resolution=camera['image_resolution'], pose=cam_pose)
light_name = bf.add_light([args.proj_x, 0, args.height])
bf.add_plane(size=100, properties=dict(physics=False, collision_shape='CONVEX_HULL'))
tote = bf.add_tote(length=args.tote_length, width=args.tote_width, height=args.tote_height,
                   properties=dict(physics=False, collision_shape='MESH'))
obj = bf.add_object_from_file(filepath=args.object_path, properties=dict(physics=True, collision_shape='CONVEX_HULL'),
                              max_vertices=2500)
pose_sampler = bf.in_tote_sampler(tote, obj, args.num)
bf.collision_avoidance_positioning(obj, pose_sampler)
for _ in range(args.num - 1):
    obj = bf.duplicate_mesh_object(obj)
    bf.collision_avoidance_positioning(obj, pose_sampler)

dump_camera_json(output_dir + '/camera.json', 'BlenderCamera', 'BlenderCamera', camera['intrinsics'],
                 camera['image_resolution'], camera['distort_coeffs'], camera['depth_scale'])
dump_env_yml(output_dir + '/env.yml', args.tote_length, args.tote_width, args.tote_height, 'BlenderCamera', cam_pose)
for i in range(args.num):
    bf.remove_highest_object()
    bf.physics_simulation(substeps_per_frame=args.substeps_per_frame)
    timestamp = int(time.time())
    prefix = '{}/{}_{}_'.format(output_dir, timestamp, args.camera_type)
    bf.render_color(prefix + 'rgb.png', denoiser='OPTIX', samples=args.samples, max_bounces=args.max_bounces)
    bf.render_depth(prefix + 'aligned_depth.png', depth_scale=camera['depth_scale'], save_npz=False)
    bf.render_light_mask(prefix + 'light_mask.png', light_name, threshold=args.nan_threshold)
    bf.apply_nan_mask(prefix + 'aligned_depth.png', prefix + 'light_mask.png', prefix + 'masked_depth.png')
