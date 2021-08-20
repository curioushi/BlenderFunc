FROM nvidia/cudagl:11.4.1-base-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update; exit 0
RUN apt-get install -y tar xz-utils vim nano
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y \
            libx11-6 \
            libxi6 \
            libxxf86vm1 \
            libxfixes3 \
            libxrender1 \
            libgl1 \
            libglib2.0-0 \
            libfreetype6 \
            libgl1-mesa-dev \
            libglu1-mesa \
            libfreeimage3

# install BlenderFunc
WORKDIR /workspace
COPY blenderfunc.tar.xz .
RUN mkdir blenderfunc
RUN tar xvf blenderfunc.tar.xz -C blenderfunc
RUN rm blenderfunc.tar.xz

# install Blender
WORKDIR /workspace/blenderfunc
COPY blender-2.92.0-linux64.tar.xz .
RUN tar xvf blender-2.92.0-linux64.tar.xz
RUN rm blender-2.92.0-linux64.tar.xz
RUN ln -s blender-2.92.0-linux64/blender .

# HACK: suppress alsa error https://github.com/cypress-io/cypress-docker-images/issues/52
COPY asound.conf /etc/asound.conf
# user tsinghua python source
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple  # use tsinghua source
# run script first time to install python depandencies and load render kernels
# enable cuda during docker build: https://stackoverflow.com/questions/59691207/docker-build-with-nvidia-runtime
RUN ./blender --background --python examples/xyz_log.py -- --output_dir=output/xyz_log --object_path=resources/models/brake_disk.ply --num=2
# HACK: make cached render kernel copyable
RUN chmod 777 /var/tmp/OptixCache_root/
