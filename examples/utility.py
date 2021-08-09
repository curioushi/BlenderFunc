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
