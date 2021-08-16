import os
import subprocess
import sys
from typing import List

from .environment import get_python_bin, get_installed_packages, get_custom_python_packages_path


def setup_custom_packages(required_packages: List = None, reinstall_packages: bool = False):
    python_bin = get_python_bin()
    packages_path = get_custom_python_packages_path()

    subprocess.Popen([python_bin, "-m", "ensurepip"]).wait()
    if not os.path.exists(packages_path):
        os.mkdir(packages_path)
    sys.path.append(packages_path)

    installed_packages = get_installed_packages()

    if required_packages is None:
        return

    # upgrade pip
    subprocess.Popen([python_bin, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'])

    for package in required_packages:
        if "==" in package:
            package_name, package_version = package.lower().split('==')
        else:
            package_name, package_version = package.lower(), None

        already_installed = package_name in installed_packages.keys()

        # remove if version not match
        if package_version is not None and already_installed:
            already_installed = (package_version == installed_packages[package_name])
            if not already_installed:
                subprocess.Popen([python_bin, "-m", "pip", "uninstall", package_name, "-y"],
                                 env=dict(os.environ, PYTHONPATH=packages_path)).wait()

        # install if not exist or force reinstall
        if not already_installed or reinstall_packages:
            print("Installing pip package {} {}".format(package_name, package_version))
            subprocess.Popen(
                [python_bin, "-m", "pip", "install", package, "--target", packages_path, "--upgrade"],
                env=dict(os.environ, PYTHONPATH=packages_path)).wait()

    installed_packages = get_installed_packages()
    print('installed_packages:')
    for name, version in installed_packages.items():
        print(" - {} {}".format(name, version))


__all__ = ["setup_custom_packages"]
