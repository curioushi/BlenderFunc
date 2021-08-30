Use Docker
=================================================

Check NVIDIA Installation
------------------------------

.. code-block:: text

    nvidia-smi

You can see the driver version and cuda version, on my computer:

.. code-block:: text

    +-----------------------------------------------------------------------------+
    | NVIDIA-SMI 470.57.02    Driver Version: 470.57.02    CUDA Version: 11.4     |
    |-------------------------------+----------------------+----------------------+
    | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
    | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
    |                               |                      |               MIG M. |
    |===============================+======================+======================|
    |   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0  On |                  N/A |
    | 40%   39C    P5    21W / 160W |    833MiB /  5932MiB |      1%      Default |
    |                               |                      |                  N/A |
    +-------------------------------+----------------------+----------------------+


Check Docker
------------------------------

.. code-block:: text

    systemctl status docker.service
    systemctl status docker.socket

Installation guide: https://docs.docker.com/engine/install/

Check NVIDIA Docker
------------------------------

.. code-block:: text

    sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

Installation guide: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker

Enable CUDA during Docker building
-------------------------------------

edit the ``/etc/docker/daemon.json`` with content:

.. code-block:: text

    {
        "runtimes": {
            "nvidia": {
                "path": "/usr/bin/nvidia-container-runtime",
                "runtimeArgs": []
            } 
        },
        "default-runtime": "nvidia" 
    }

restart docker daemon:

.. code-block:: text

    sudo systemctl restart docker

Reference: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker


Build Docker
-------------------------

.. code-block:: shell

    cd docker
    ./build

Run Docker
--------------------------

Currently, docker can only be used to generate data in xyz_log format.

You can use docker like a CLI tool:


.. code-block:: shell

    ./run --help
    ./run --output_dir=$(pwd)/xyz_log

.. code-block:: text

    usage: blender [-h] [--output_dir OUTPUT_DIR] [--camera_type CAMERA_TYPE]
                [--camera_height CAMERA_HEIGHT] [--obstruction OBSTRUCTION]
                [--tote_length TOTE_LENGTH] [--tote_width TOTE_WIDTH]
                [--tote_height TOTE_HEIGHT] [--tote_thickness TOTE_THICKNESS]
                [--model_path MODEL_PATH] [--max_faces MAX_FACES]
                [--num_begin NUM_BEGIN] [--num_end NUM_END]
                [--num_pick NUM_PICK] [--max_bounces MAX_BOUNCES]
                [--samples SAMPLES] [--substeps_per_frame SUBSTEPS_PER_FRAME]
                [--enable_perfect_depth] [--enable_instance_segmap]
                [--enable_class_segmap] [--enable_mesh_info]

    optional arguments:
    -h, --help            show this help message and exit
    --output_dir OUTPUT_DIR
                            output directory, the folder will be automatically
                            created if not exist
    --camera_type CAMERA_TYPE
                            different cameras have different fov and aspect ratio:
                            Photoneo-M | Photoneo-L | XYZ-SL(default)
    --camera_height CAMERA_HEIGHT
                            camera height in meter, default: 2
    --obstruction OBSTRUCTION
                            control the number of obstructed points, reasonable
                            range 0~0.4, default: 0.2
    --tote_length TOTE_LENGTH
                            tote x-axis dimension, default: 0.7
    --tote_width TOTE_WIDTH
                            tote y-axis dimension, default: 0.7
    --tote_height TOTE_HEIGHT
                            tote z-axis dimension, default: 0.5
    --tote_thickness TOTE_THICKNESS
                            tote thickness, default: 0.03
    --model_path MODEL_PATH
                            CAD model, supported format: ply, stl
    --max_faces MAX_FACES
                            decimate mesh if the number of faces of mesh is bigger
                            than this value, default: 10000
    --num_begin NUM_BEGIN
                            number of objects at the beginning, default: 30
    --num_end NUM_END     number of objects in the end, default: 0
    --num_pick NUM_PICK   number of objects picked each time, default: 5
    --max_bounces MAX_BOUNCES
                            render option: max bounces of light, default: 3
    --samples SAMPLES     render option: samples for each pixel, default: 10
    --substeps_per_frame SUBSTEPS_PER_FRAME
                            physics option: higher value for higher simulation
                            stability, default: 10
    --enable_perfect_depth
                            flag: render depth without obstruction
    --enable_instance_segmap
                            flag: render instance segmentation map
    --enable_class_segmap
                            flag: render class segmentation map
    --enable_mesh_info    flag: write mesh information including poses