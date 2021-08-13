import os
import bpy
import time

BLENDER_FUNC_STACK_DEPTH = 0


def blender_func(func):
    def wrapper(*func_args, **func_kwargs):
        global BLENDER_FUNC_STACK_DEPTH
        print('{}Start: {}'.format('  ' * BLENDER_FUNC_STACK_DEPTH, func.__name__))
        BLENDER_FUNC_STACK_DEPTH += 1
        t1 = time.time()
        func(*func_args, **func_kwargs)
        t2 = time.time()
        BLENDER_FUNC_STACK_DEPTH -= 1
        duration = t2 - t1
        if duration < 1:
            time_string = f'{duration * 1000:.0f} ms'
        else:
            time_string = f'{duration:.2f} s'
        print('{}Finish: {}, {}'.format('  ' * BLENDER_FUNC_STACK_DEPTH, func.__name__, time_string))

    return wrapper


def save_blend(filepath='/tmp/temp.blend'):
    output_dir = os.path.dirname(filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(filepath):
        os.remove(filepath)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, relative_remap=False)


def seconds_to_frames(seconds: float) -> int:
    return int(seconds * bpy.context.scene.render.fps)


def frames_to_seconds(frames: int) -> float:
    return float(frames) / bpy.context.scene.render.fps


def get_object_by_name(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name, None)
    if obj:
        return obj
    else:
        raise Exception('Object "{}" does not exist'.format(name))


def get_material_by_name(name: str) -> bpy.types.Material:
    obj = bpy.data.materials.get(name, None)
    if obj:
        return obj
    else:
        raise Exception('Material "{}" does not exist'.format(name))


__all__ = ['save_blend', 'get_material_by_name', 'get_object_by_name']
