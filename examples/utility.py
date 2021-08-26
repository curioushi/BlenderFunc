import blenderfunc as bf
bf.setup_custom_packages(['xmltodict'])
import xmltodict
import numpy as np


def parse_camera_xml(filepath):
    # load xml as dict
    with open(filepath, 'r') as f:
        data = xmltodict.parse(f.read())
        data = data['opencv_storage']

    # parse dict
    ret = dict()
    for key in data.keys():
        if '@type_id' in data[key] and data[key]['@type_id'] == 'opencv-matrix':
            rows = int(data[key]['rows'])
            cols = int(data[key]['cols'])
            matrix = np.array([float(x) for x in data[key]['data'].split()]).reshape(rows, cols)
            if cols == 1 or rows == 1:
                matrix = matrix.reshape(-1)
            ret[key] = matrix.tolist()
        else:
            ret[key] = [float(x) for x in data[key].split()]

    return ret


def compute_structured_light_params(filepath: str, cam_height=1.5):
    sl_param = parse_camera_xml(filepath)

    cam_intr = sl_param['CameraIntrinsics']
    image_resolution = sl_param['ImageSize']
    cam_distort = sl_param['CameraDistCoeffs']
    proj_intr = sl_param['ProjectorIntrinsics']
    proj_distort = sl_param['ProjectorDistCoeffs']
    rot = np.array(sl_param['Rotation'])
    translation = np.array(sl_param['Translation']) / 1000
    cam2proj = np.hstack([rot, translation.reshape(-1, 1)])
    cam2proj = np.vstack([cam2proj, np.array([0, 0, 0, 1])])
    cam2world = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, cam_height], [0, 0, 0, 1]])
    proj2world = cam2world.dot(np.linalg.inv(cam2proj))

    return cam_intr, image_resolution, cam_distort, proj_intr, proj_distort, cam2world.tolist(), proj2world.tolist()
