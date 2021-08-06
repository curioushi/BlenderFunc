import bpy


def clean_data():
    """remove all data except the default scene"""
    for collection in dir(bpy.data):
        data_structure = getattr(bpy.data, collection)
        if isinstance(data_structure, bpy.types.bpy_prop_collection) and hasattr(data_structure, "remove"):
            for block in data_structure:
                if not isinstance(block, bpy.types.Scene) or block.name != "Scene":
                    data_structure.remove(block)


__all__ = ['clean_data']
