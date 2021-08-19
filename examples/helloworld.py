import sys
sys.path.append('.')
from blenderfunc.utility.custom_packages import setup_custom_packages
setup_custom_packages(["numpy", "Pillow", "opencv-python", "imageio"])

import blenderfunc.all as bf

bf.initialize()
bf.set_background_light(color=[0.5, 0.5, 0.5], strength=1)
bf.add_plane(10)
cube_name = bf.add_cube(1)
bf.get_object_by_name(cube_name).location = (0, 0, 0.5)
bf.set_camera(pose=[[-0.6440926790237427, 0.6483752727508545, -0.40589916706085205, 1.6972744464874268],
                    [0.7560893297195435, 0.45909714698791504, -0.4664319157600403, 1.8544113636016846],
                    [-0.1160757914185524, -0.6073213815689087, -0.7859307527542114, 2.6100692749023438],
                    [0.0, 0.0, 0.0, 1.0]])
bf.render_color('output/helloworld/output.png', denoiser='NLM', save_blend_file=True)
