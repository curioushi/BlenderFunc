#!/bin/bash

script_dir="$(dirname $(realpath "$0"))"
repo_dir="$script_dir/../"

docker run --gpus=all -it --user `id -u $USER`:`id -u $USER` \
           -v /etc/passwd:/etc/passwd \
           -v /home/$USER:/home/$USER \
           blenderfunc:latest \
           /bin/bash -c "cp -r /var/tmp/OptixCache_root /var/tmp/OptixCache_$USER && \
                         ./blender -b --python examples/xyz_log.py -- \
                         --output_dir=$repo_dir/output/xyz_log \
                         --object_path=$repo_dir/resources/models/brake_disk.ply"