import bpy

prefs = bpy.context.preferences
cprefs = prefs.addons['cycles'].preferences
cprefs.get_devices()
for i, device in enumerate(cprefs.devices):
    print(i, device.name)