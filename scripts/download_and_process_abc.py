import os
import subprocess
import argparse
import hashlib
import yaml
import shutil


def check_md5(filepath, md5):
    with open(filepath, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    pred_md5 = file_hash.hexdigest()
    return pred_md5 == md5


# multiple process run
# for i in {0..99};do echo $i;done | xargs -n 1 -P 6 sh -c 'python scripts/download_and_process_abc.py --abc_index=$0'
parser = argparse.ArgumentParser()
parser.add_argument('--dataset_dir', type=str, default='resources/abc')
parser.add_argument('--abc_index', type=int, default=0, help='0 ~ 99')
args = parser.parse_args()
if args.abc_index < 0 or args.abc_index > 99:
    raise Exception('abc_index should be 0 ~ 99')

with open('scripts/abc_stl2_infos.yml', 'r') as f:
    abc_info = yaml.load(f, Loader=yaml.FullLoader)

abc_index = '{:04}'.format(args.abc_index)
dataset_dir = args.dataset_dir
os.makedirs(dataset_dir, exist_ok=True)
download_dir = os.path.join(dataset_dir, "download")
os.makedirs(download_dir, exist_ok=True)
extract_dir = os.path.join(dataset_dir, "extract")
os.makedirs(extract_dir, exist_ok=True)
process1_dir = os.path.join(dataset_dir, "process1")
os.makedirs(process1_dir, exist_ok=True)

filename = 'abc_{}_stl2_v00.7z'.format(abc_index)
url = abc_info[filename]['url']
md5 = abc_info[filename]['md5']

# download
download_filepath = os.path.join(download_dir, filename)
while True:
    check_success = False
    if os.path.exists(download_filepath):
        check_success = check_md5(download_filepath, md5)
        if check_success:
            print('md5 check success, next step')
            break
    if not check_success:
        print('md5 check failed, download again')
        subprocess.Popen(['wget', '--no-check-certificate', url, '-O', os.path.join(download_dir, filename)]).wait()

# extract 7zip
extract_output_dir = os.path.join(extract_dir, os.path.splitext(filename)[0])
subprocess.Popen(['7z', '-y', 'x', download_filepath, '-o{}'.format(extract_output_dir)]).wait()

# process CAD models
process1_output_dir = os.path.join(process1_dir, os.path.splitext(filename)[0])
subprocess.Popen(['blender', '--background', '--python', 'examples/abc_process.py', '--',
                  '--input_dir={}'.format(extract_output_dir),
                  '--output_dir={}'.format(process1_output_dir)]).wait()

# remove redundant files
os.remove(download_filepath)
shutil.rmtree(extract_output_dir)
