# BlenderFunc

This repo was inspired by BlenderProc: https://github.com/DLR-RM/BlenderProc.git

The differences between this project and BlenderProc are:

- Instead of writing config in BlenderProc, you can directly write python script to control the data generation process, 
  which gives you more flexibility

- Simple but powerful functions, e.g., `clean_data()`, `set_camera()`, `set_object` to help you write scripts


Best practice pseudocode:
```
for frame in frames:
    clean_scene()
    set_object()
    set_texture()
    set_projector()
    set_camera()
    set_renderer()
    render()
    save_blend()
```