import bpy
from typing import List, Tuple


def add_light(location: List[float] = [0, 0, 1], energy: float = 10, name: str = 'Light') -> str:
    bpy.ops.object.light_add(type='POINT', location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    obj.data.energy = energy
    return obj.name


__all__ = ['add_light']
