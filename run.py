import sys

sys.path.append('.')

import blenderfunc as bf

bf.setup_custom_packages(["numpy"])
bf.clean_data()
bf.set_camera(
    pose=[[1, 0, 0, 0],
          [0, -1, 0, 0],
          [0, 0, -1, 2],
          [0, 0, 0, 1]]
)
