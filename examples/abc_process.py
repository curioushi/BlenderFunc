import sys
sys.path.append('.')
import os
import sys
import argparse
import blenderfunc as bf
from tqdm import tqdm
from glob import glob


def parse_arguments():
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, default='abc_0000_stl2_v00',
                        help='abc dataset folder, example: abc_xxxx_stl2_v00')
    parser.add_argument('--output_dir', type=str, default='output',
                        help='output_dir')
    args = parser.parse_args(args=argv)
    return args


args = parse_arguments()
bf.initialize()
bf.initialize_folder(args.output_dir, clear_files=False)
input_files = sorted(list(glob(os.path.join(args.input_dir, '*', '*.stl'))))
input_file = None
for input_file in tqdm(input_files, position=0, leave=True):
    try:
        bf.initialize()
        print('-' * 80)
        print('Process file: {}'.format(input_file))
        index = os.path.basename(os.path.dirname(input_file))
        output_file = os.path.join(args.output_dir, '{}.stl'.format(index))

        if os.path.getsize(input_file) > 20000000:
            print('File too big, ignored')
            os.remove(input_file)
            continue

        obj_name = bf.add_object_from_file(input_file)
        objs = bf.separate_isolated_meshes(obj_name)

        if len(objs) != 1:
            print('More than one part, ignored')
            os.remove(input_file)
            continue

        bf.decimate_mesh_object(obj_name, max_faces=10000)
        bf.export_mesh_object(output_file, obj_name, center_of_mass=True)
        os.remove(input_file)
    except:
        pass

# check if all files are processed
f = open(os.path.join(args.output_dir, 'exit_status'), 'w')
if input_file == input_files[-1]:
    f.write('Done\n')
else:
    f.write('{}\n'.format(input_file))
f.close()
