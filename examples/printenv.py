import sys
sys.path.append('.')
import blenderfunc as bf
import bpy

print()
print("get_blender_path() =", bf.get_blender_path())
print("get_blender_version() =", bf.get_blender_version())
print("get_pre_python_packages_path() =", bf.get_pre_python_packages_path())
print("get_custom_python_packages_path() =", bf.get_custom_python_packages_path())
print("get_python_bin_folder() =", bf.get_python_bin_folder())
print("get_python_bin() =", bf.get_python_bin())
print("get_installed_packges() = ")
pkgs = bf.get_installed_packages()
for name, version in pkgs.items():
    print('    ', name, version)

prefs = bpy.context.preferences
cprefs = prefs.addons['cycles'].preferences
cprefs.get_devices()
print('Devices:')
for i, device in enumerate(cprefs.devices):
    print('    ', i, device.name)