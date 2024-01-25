# BlenderFunc

[Online Documentation](https://blenderfunc.readthedocs.io/en/latest/)

This repo was inspired by BlenderProc: https://github.com/DLR-RM/BlenderProc.git

The differences between this project and BlenderProc:

- Instead of writing config in BlenderProc, you can directly write python script to control the data generation process, 
  which gives you more flexibility

- Simple but powerful functions, e.g., `set_camera()`, `set_projector()`, `add_ply()`, 
  `physics_simulation()`, `render_color()`

## How to run

```shell
cd BlenderFunc

## install Blender 2.93
wget https://mirrors.tuna.tsinghua.edu.cn/blender/blender-release/Blender2.93/blender-2.93.9-linux-x64.tar.xz
tar xvf blender-2.93.9-linux-x64.tar.xz
ln -s blender-2.93.9-linux-x64/blender .

## run helloworld.py
./blender --background --python examples/helloworld.py
```

## Use docker to generate xyz_log
```shell
## build docker
./docker/build.sh

## run docker
# help
./docker/run.sh --help

# generate data to specified directory (WARNING: please use absolute path)
./docker/run.sh --output_dir=$(pwd)/xyz_log

# for convenience, you can copy this script to /usr/local/bin
sudo cp ./docker/run.sh /usr/local/bin/synthesize_xyz_log
synthesize_xyz_log --output_dir=$(pwd)/xyz_log
```

## Todo

### features
- [x] shadow map
- [x] add_simple_texture
- [x] support BW output
- [x] material location, rotation, scale, main color
- [x] save_blend_file for each renderer
- [x] class segmap
- [x] instance segmap
- [x] normal
- [x] pose output
- [x] hdr downloader
- [x] hdr texture
- [x] camera distortion
- [x] projector distortion
- [x] docker image
- [x] ABC dataset download
- [x] ABC dataset process
- [x] calibration pipeline
- [x] support stl model
- [x] upgrade collision checking
- [ ] pose sampler return same format
- [x] xyz-log format
- [ ] coco format
- [x] documentation

### bugs
- [x] physics simulation origin wrong
- [x] fail to enable GPU
- [ ] set object.name to an existed name