import sys
sys.path.append('.')
import blenderfunc as bf
import os
import cv2
import imageio
import argparse
import numpy as np
from tqdm import tqdm
from glob import glob


def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = ((w - 1) / 2, (h - 1) / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1)
    rotated = cv2.warpAffine(image, M, (w, h), cv2.INTER_CUBIC)
    return rotated


def normalize_image(img):
    if img.ndim == 3:
        img = img[:, :, 0]
    img = img.astype(np.float32)
    img = (img - img.min()) / (img.max() - img.min())
    return img


def compute_symmetry(image_file, diff_threshold=0.01, mask_threshold=0.05, symmetry_threshold=0.001):
    img = imageio.imread(image_file)
    img = normalize_image(img)

    candidate_folds = [1, 2, 3, 4, 5, 6, 8, 10, 12]
    candidate_angles = [360 / fold for fold in candidate_folds]
    rotated_imgs = np.array([rotate_image(img, angle) for angle in candidate_angles]).astype(np.float32)
    rotated_imgs = (rotated_imgs - np.min(rotated_imgs)) / (np.max(rotated_imgs) - np.min(rotated_imgs))

    diff_imgs = (np.abs(rotated_imgs - rotated_imgs[0]) > diff_threshold).astype(np.float32)

    # opening diff images to denoise
    kernel = np.ones((4, 4), np.uint8)
    for i in range(len(diff_imgs)):
        diff_imgs[i] = cv2.erode(diff_imgs[i], kernel)

    diff_ratios = np.sum(np.sum(diff_imgs, axis=-1), axis=-1) / (2 * np.sum(img > mask_threshold))

    # print(candidate_folds)
    # print(diff_ratios)
    # for ratio, diff in zip(diff_ratios, diff_imgs):
    #     print(ratio)
    #     cv2.imshow("diff", diff)
    #     cv2.waitKey(0)

    fold = 1
    for i, fo in enumerate(candidate_folds):
        if diff_ratios[i] < symmetry_threshold:
            fold = fo
    if np.sum(diff_ratios < symmetry_threshold) == len(candidate_folds):
        fold = 360

    viz_img = (img * 255).astype(np.uint8)
    cv2.putText(viz_img, 'fold = {}'.format(fold), (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.6, 255)
    imageio.imwrite(image_file, viz_img)

    return fold


def merge_image(file1, file2, file3, file4, output_filename):
    img1 = normalize_image(imageio.imread(file1))
    img2 = normalize_image(imageio.imread(file2))
    img3 = normalize_image(imageio.imread(file3))
    img4 = normalize_image(imageio.imread(file4))
    merged = np.vstack([np.hstack([img1, img2]), np.hstack([img3, img4])])
    imageio.imwrite(output_filename, merged)
    os.remove(file1)
    os.remove(file2)
    os.remove(file3)
    os.remove(file4)


def parse_arguments():
    # ignore arguments before '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, default='output/symmetry')
    parser.add_argument('--model_files', type=str, default='resources/models/brake_disk.ply')
    args = parser.parse_args(args=argv)

    if "*" in args.model_files:
        args.model_files = sorted(glob(args.model_files))
    else:
        args.model_files = [args.model_files]
    return args


camera_poses = {
    "+x": [[0, 0, -1, 1],
           [1, 0, 0, 0],
           [0, -1, 0, 0],
           [0, 0, 0, 1]],
    "-y": [[1, 0, 0, 0],
           [0, 0, 1, -1],
           [0, -1, 0, 0],
           [0, 0, 0, 1]],
    "+z": [[1, 0, 0, 0],
           [0, -1, 0, 0],
           [0, 0, -1, 1],
           [0, 0, 0, 1]],
    "+view": [[0.691194474697113, 0.5020413994789124, -0.519802451133728, 0.5208610892295837],
              [0.7224580645561218, -0.49740657210350037, 0.48024144768714905, -0.4802001714706421],
              [-0.017452405765652657, -0.7074756622314453, -0.7065085172653198, 0.705771267414093],
              [0.0, 0.0, 0.0, 1.0]]
}
args = parse_arguments()

bf.initialize_folder(args.output_dir, clear_files=False)

for model_file in tqdm(args.model_files):
    bf.initialize()

    # load model
    model_name = os.path.splitext(os.path.basename(model_file))[0]
    # if model_name != '00000172':
    #     continue
    obj_name = bf.add_object_from_file(model_file)
    obj = bf.get_object_by_name(obj_name)
    bf.set_origin_to_center_of_mass(obj_name, 'VOLUME')
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)

    # determine ortho-camera zoom
    vertices = np.array([v.co for v in obj.data.vertices])
    min_bound = np.min(vertices, axis=0)
    max_bound = np.max(vertices, axis=0)
    ortho_scales = 2 * np.maximum(np.abs(min_bound), np.abs(max_bound))

    img_grid = [None] * 4
    folds = [None] * 3
    for pose_name, pose in camera_poses.items():
        image_filepath = os.path.join(args.output_dir, "{}{}.png".format(model_name, pose_name))
        # HACK: use ortho camera and zoom to object
        cam_name = bf.set_camera(pose=pose, image_resolution=[512, 512])
        cam = bf.get_object_by_name(cam_name).data
        cam.type = 'ORTHO'
        cam.shift_x = 0
        cam.shift_y = 0
        if 'x' in pose_name:
            cam.ortho_scale = 1.42 * max(ortho_scales[1], ortho_scales[2])
            img_grid[3] = image_filepath
        elif 'y' in pose_name:
            cam.ortho_scale = 1.42 * max(ortho_scales[0], ortho_scales[2])
            img_grid[0] = image_filepath
        elif 'z' in pose_name:
            cam.ortho_scale = 1.42 * max(ortho_scales[0], ortho_scales[1])
            img_grid[1] = image_filepath
        else:
            cam.ortho_scale = 1.73 * max(ortho_scales)
            img_grid[2] = image_filepath

        bf.remove_all_materials()
        bf.remove_all_lights()
        if 'view' in pose_name:
            bf.add_light(location=[0, 0, 1])
            bf.set_background_light(strength=0.1)
        else:
            mat_name = bf.add_transparent_material(emission_strength=5)
            bf.set_material(obj_name, mat_name)

        # render image & compute symmetry
        bf.render_color(image_filepath, save_blend_file=False,
                        denoiser='OPTIX', max_bounces=4, samples=100, color_mode='BW', color_depth=16)
        if 'view' not in pose_name:
            fold = compute_symmetry(image_filepath)
            if 'x' in pose_name:
                folds[0] = fold
            elif 'y' in pose_name:
                folds[1] = fold
            elif 'z' in pose_name:
                folds[2] = fold

    merge_image(img_grid[0], img_grid[1], img_grid[2], img_grid[3],
                os.path.join(args.output_dir, "{}_{}_{}_{}.png".format(model_name, folds[0], folds[1], folds[2])))
