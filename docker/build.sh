#!/bin/bash

# change working directory to script directory
cd "$(dirname "$0")"

# download blender if doesn't exist
if [ ! -e "blender-2.92.0-linux64.tar.xz" ]; then
  wget https://download.blender.org/release/Blender2.92/blender-2.92.0-linux64.tar.xz
fi

# compress all not-ignored files in this repository
if [ ! -e "blenderfunc.tar.xz" ]; then
  git ls-files .. -z | xargs -0 tar -czvf blenderfunc.tar.xz
fi

docker build -t blenderfunc:latest .