from typing import List
import bpy
from blenderfunc.object.collector import get_all_mesh_objects


def physics_simulation(mesh_objects: List[bpy.data.objects] = None):
    if mesh_objects is None:
        mesh_objects = get_all_mesh_objects()


