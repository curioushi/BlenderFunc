import os
import subprocess
import sys

blender_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", ".."))
blender_version = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..")))
python_bin_folder = os.path.join(blender_path, blender_version, "python", "bin")
python_bin = os.path.join(python_bin_folder, "python3.7m")
pre_python_packages_path = os.path.join(python_bin_folder, "..", "lib", "python3.7", "site-packages")
custom_python_packages_path = os.path.abspath(os.path.join(blender_path, 'custom-python-packages'))


def get_blender_path() -> str:
    """Get root path to blender software"""
    return blender_path


def get_blender_version() -> str:
    """Get the version of blender"""
    return blender_version


def get_custom_python_packages_path() -> str:
    """Get the path to the custom python packages of Blender"""
    return custom_python_packages_path


def get_pre_python_packages_path() -> str:
    """Get the path to the previous python packages of Blender"""
    return pre_python_packages_path


def get_python_bin_folder() -> str:
    """Get the python bin folder of Blender"""
    return python_bin_folder


def get_python_bin() -> str:
    """Get the python binary path of Blender"""
    return python_bin


def get_installed_packages() -> dict:
    """Get the installed packages in previous and custom python packages path

    :return: The installed python packages
    :rtype: dict, key=package_name, val=package_version
    """
    installed_packages = subprocess.check_output(
        [python_bin, "-m", "pip", "list", "--format=freeze", "--path={}".format(pre_python_packages_path)])
    installed_packages += subprocess.check_output(
        [python_bin, "-m", "pip", "list", "--format=freeze", "--path={}".format(custom_python_packages_path)])
    installed_packages_name, installed_packages_versions = zip(
        *[str(line).lower().split('==') for line in installed_packages.splitlines()])
    installed_packages_name = [ele[2:] if ele.startswith("b'") else ele for ele in installed_packages_name]
    installed_packages_versions = [ele[:-1] if ele.endswith("'") else ele for ele in installed_packages_versions]
    installed_packages = dict(zip(installed_packages_name, installed_packages_versions))
    return installed_packages


__all__ = ["get_installed_packages", "get_pre_python_packages_path", "get_custom_python_packages_path",
           "get_python_bin", "get_python_bin_folder", "get_blender_path", "get_blender_version"]
