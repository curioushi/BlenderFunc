import sys

sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages

setup_custom_packages(["numpy", "Pillow", "xmltodict", "matplotlib"])

import blenderfunc.all as bf
import matplotlib.pyplot as plt
import numpy as np
import json
import yaml
import os
import time
import imageio
import subprocess
import shutil
from glob import glob
from examples.utility import compute_structured_light_params


def rebuild_depth(sequence_path: str,
                  camera_cfg_path: str,
                  output_depth_filepath: str,
                  output_cloud_filepath: str):
    sequence_path = os.path.abspath(sequence_path)
    camera_cfg_path = os.path.abspath(camera_cfg_path)
    output_depth_filepath = os.path.abspath(output_depth_filepath)
    output_cloud_filepath = os.path.abspath(output_cloud_filepath)
    rebuilder_bin = 'rebuild_depth'
    cfg_path = '/usr/local/etc/StructuredLight.json'
    with open(cfg_path, 'r') as f:
        data = json.load(f)
        data['rebuilder']['calibration_res_path'] = camera_cfg_path

    timestamp = int(time.time())
    temp_json_path = '/tmp/{}.json'.format(timestamp)
    with open(temp_json_path, 'w') as f:
        json.dump(data, f)

    cwd = os.getcwd()
    os.chdir(sequence_path)
    subprocess.Popen(
        [rebuilder_bin, '-i={}/'.format(sequence_path), '-c={}'.format(temp_json_path)]).wait()
    shutil.move('depth_img.png', output_depth_filepath)
    shutil.move('organized_cloud.pcd', output_cloud_filepath)
    os.chdir(cwd)


def error_analysis(gt_depth_filepath: str,
                   light_mask_filepath: str,
                   light_shadow_mask_filepath: str,
                   rebuild_depth_filepath: str,
                   dist_threshold: float = 1):
    output_dir = os.path.dirname(gt_depth_filepath)
    gt_depth = imageio.imread(gt_depth_filepath).astype(np.float32) * 0.05
    light_region = imageio.imread(light_mask_filepath) > 127
    light_region_with_shadow = imageio.imread(light_shadow_mask_filepath) > 127
    light_mask = light_region & light_region_with_shadow
    shadow_mask = light_region & ~light_region_with_shadow
    rebuild_depth = imageio.imread(rebuild_depth_filepath).astype(np.float32) * 0.05
    rebuild_nan = rebuild_depth == 0

    error = gt_depth - rebuild_depth

    light_error = np.copy(error)
    light_error[~light_mask | rebuild_nan] = float('nan')
    light_good_mask = np.abs(light_error) < dist_threshold
    light_bad_mask = np.abs(light_error) >= dist_threshold
    light_nan_mask = light_mask & rebuild_nan

    shadow_error = np.copy(error)
    shadow_error[~shadow_mask | rebuild_nan] = float('nan')
    shadow_good_mask = np.abs(shadow_error) < dist_threshold
    shadow_bad_mask = np.abs(shadow_error) >= dist_threshold
    shadow_nan_mask = shadow_mask & rebuild_nan

    total = float(np.sum(light_region))
    light_num = float(np.sum(light_mask))
    light_good_num = float(np.sum(light_good_mask))
    light_bad_num = float(np.sum(light_bad_mask))
    light_nan_num = float(np.sum(light_nan_mask))
    shadow_num = float(np.sum(shadow_mask))
    shadow_good_num = float(np.sum(shadow_good_mask))
    shadow_bad_num = float(np.sum(shadow_bad_mask))
    shadow_nan_num = float(np.sum(shadow_nan_mask))

    data = {
        "light": light_num / total,
        "light_good": light_good_num / total,
        "light_bad": light_bad_num / total,
        "light_nan": light_nan_num / total,
        "shadow": shadow_num / total,
        "shadow_good": shadow_good_num / total,
        "shadow_bad": shadow_bad_num / total,
        "shadow_nan": shadow_nan_num / total,
    }
    with open(output_dir + '/error.yml', 'w') as f:
        yaml.dump(data, f)

    light_error[~light_mask | rebuild_nan] = 0
    plt.imsave(output_dir + '/light_error.png', light_error, cmap='bwr', vmin=-dist_threshold, vmax=dist_threshold)
    plt.imsave(output_dir + '/light_good_mask.png', light_good_mask, cmap='gray')
    plt.imsave(output_dir + '/light_bad_mask.png', light_bad_mask, cmap='gray')
    plt.imsave(output_dir + '/light_nan_mask.png', light_nan_mask, cmap='gray')

    shadow_error[~shadow_mask | rebuild_nan] = 0
    plt.imsave(output_dir + '/shadow_error.png', shadow_error, cmap='bwr', vmin=-dist_threshold, vmax=dist_threshold)
    plt.imsave(output_dir + '/shadow_good_mask.png', shadow_good_mask, cmap='gray')
    plt.imsave(output_dir + '/shadow_bad_mask.png', shadow_bad_mask, cmap='gray')
    plt.imsave(output_dir + '/shadow_nan_mask.png', shadow_nan_mask, cmap='gray')


camera_config_path = 'resources/sl_param_no_distortion.xml'
cam_K, image_resolution, cam_distort, proj_K, proj_distort, cam2world, proj2world = \
    compute_structured_light_params(camera_config_path, 2)
proj_patterns = sorted(glob('resources/images/sl_patterns/*.bmp'))

for metallic in [0.0, 0.25, 0.5, 0.75, 1.0]:
    for roughness in [0.1, 0.3, 0.5, 0.7, 0.9]:
        for max_bounces in [0, 8]:
            output_dir = 'output/sl_texture_exp/b{}_m{}_r{}'.format(max_bounces, int(metallic * 100),
                                                                    int(roughness * 100))
            bf.initialize_folder(output_dir)
            bf.initialize()
            bf.add_plane(10)
            radius = 0.1
            for i, x in enumerate(np.linspace(-2 * radius, 2 * radius, 3)):
                for j, y in enumerate(np.linspace(-2 * radius, 2 * radius, 3)):
                    if i == 0 and j == 0:
                        obj_name = bf.add_ball(radius=radius, subdivisions=5)
                        mat_name = bf.add_simple_material([1, 1, 1], metallic=metallic, roughness=roughness)
                        bf.set_material(obj_name, mat_name)
                    else:
                        obj_name = bf.duplicate_mesh_object(obj_name)
                    bf.get_object_by_name(obj_name).location = (x, y, radius)
            bf.set_camera(opencv_matrix=cam_K, image_resolution=image_resolution, distort_coeffs=cam_distort,
                          pose=cam2world)
            proj_name = bf.set_projector(opencv_matrix=proj_K, distort_coeffs=proj_distort, image_path=proj_patterns[0],
                                         pose=proj2world, max_bounces=0)

            for i, pattern_path in enumerate(proj_patterns):
                proj_name = bf.set_projector(opencv_matrix=proj_K, distort_coeffs=proj_distort, image_path=pattern_path,
                                             pose=proj2world, max_bounces=max_bounces)
                bf.render_color(output_dir + '/{:04}.png'.format(i), samples=128, denoiser="OPTIX",
                                max_bounces=max_bounces, color_mode='BW', save_blend_file=True if i == 0 else False)
            bf.render_depth(output_dir + '/gt_depth.png')
            rebuild_depth(output_dir, camera_config_path, output_dir + '/rebuild_depth.png',
                          output_dir + '/rebuild_cloud.pcd')
            bf.render_light_mask(output_dir + '/light_mask.png', proj_name, cast_shadow=False)
            bf.render_light_mask(output_dir + '/light_shadow_mask.png', proj_name)
            error_analysis(output_dir + '/gt_depth.png', output_dir + '/light_mask.png',
                           output_dir + '/light_shadow_mask.png',
                           output_dir + '/rebuild_depth.png')
