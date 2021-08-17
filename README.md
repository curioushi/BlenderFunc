# BlenderFunc

This repo was inspired by BlenderProc: https://github.com/DLR-RM/BlenderProc.git

The differences between this project and BlenderProc are:

- Instead of writing config in BlenderProc, you can directly write python script to control the data generation process, 
  which gives you more flexibility

- Simple but powerful functions, e.g., `set_camera()`, `set_projector()`, `add_ply()`, 
  `physics_simulation()`, `render_color()`

## How to run

```shell
blender --background --python examples/helloworld.py
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
- [ ] ABC dataset download
- [ ] ABC dataset process
- [x] calibration pipeline
- [x] support stl model
- [ ] upgrade collision checking
- [ ] special format convert: coco, xyz-log
- [ ] documentation

### bugs
- [x] physics simulation origin wrong
- [x] fail to enable GPU