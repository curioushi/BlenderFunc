import bpy
from typing import List


def set_background_light(color: List[float] = None, strength: float = 1.0):
    """Set background lighting

    :param color: light color, black=[0,0,0], white=[1,1,1]
    :type color: List of float
    :param strength: light strength
    :type strength: float
    """
    for world in bpy.data.worlds:
        bpy.data.worlds.remove(world)
    bpy.ops.world.new()
    world = bpy.data.worlds['World']
    bpy.data.scenes['Scene'].world = world

    if color is None:
        color = [0.05, 0.05, 0.05, 1]
    elif len(color) == 3:
        color.append(1)
    world.node_tree.nodes['Background'].inputs['Color'].default_value = color
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = strength


def add_light(location: List[float] = [0, 0, 1], energy: float = 10, name: str = 'Light') -> str:
    """Add a point light source to the scene

    :param location: location of light
    :type location: List of float
    :param energy: light energy
    :type energy: float
    :param name: object_name
    :type name: str
    :return: object_name
    :rtype: str
    """
    bpy.ops.object.light_add(type='POINT', location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    obj.data.energy = energy
    return obj.name


__all__ = ['add_light', 'set_background_light']
