#!/bin/bash
# WARNING: please use absolute path in arguments !!!
# example: run.sh --output_dir=/home/$USER/Downloads/xyz_log

docker run --gpus=all -it --user `id -u $USER`:`id -u $USER` \
           -v /etc/passwd:/etc/passwd \
           -v /home/$USER:/home/$USER \
           blenderfunc:latest \
           /bin/bash -c "cp -r /var/tmp/OptixCache_root /var/tmp/OptixCache_$USER && \
                         ./blender -b --python examples/xyz_log.py -- $@"