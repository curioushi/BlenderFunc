import subprocess
from glob import glob
from tqdm import tqdm
from multiprocessing import Pool

def process_task(paths):
    box_json_path, container_stl_path = paths
    index = box_json_path.split('/')[-1].split('.')[0].split('_')[-1]
    subprocess.Popen([
        './blender', '--background', '--python', 'examples/container.py', '--',
        f'--output_dir=output/container/{index}',
        f'--boxes_data_path={box_json_path}',
        f'--container_path={container_stl_path}'
    ]).wait()

if __name__ == '__main__':
    boxes_json_paths = sorted(glob('resources/Container1K/*.json'))
    container_stl_paths = sorted(glob('resources/Container1K/*.stl'))

    for box_json_path, container_stl_path in zip(boxes_json_paths, container_stl_paths):
        index1 = box_json_path.split('/')[-1].split('.')[0].split('_')[-1]
        index2 = container_stl_path.split('/')[-1].split('.')[0].split('_')[-1]
        assert index1 == index2

    paths = list(zip(boxes_json_paths, container_stl_paths))

    with Pool(processes=4) as pool:
        for _ in tqdm(pool.imap_unordered(process_task, paths), total=len(paths)):
            pass

