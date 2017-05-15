import setuptools
import subprocess
from setuptools import setup, Command
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop


def setupInstall(cmd):
    subprocess.call(["./setup_phy.sh", cmd], shell=False)


def UninstallCommand():
    subprocess.call("./uninstall_phy.sh", shell=True)


class CustomDevelop(_develop):
    def run(self):
        setupInstall('develop')
        _develop.run(self)


class CustomInstall(_install):
    def run(self):
        setupInstall('install')
        _install.run(self)


class CustomUninstall(_install):
    def run(self):
        UninstallCommand()


cmdclass = {'install': CustomInstall,
            'develop': CustomDevelop,
            'uninstall': CustomUninstall}

long_description = open("README.md").read()

setup(name="phy-dev",
      version='0.1',
      entry_points=None,
      author="CINPLA",
      author_email="",
      maintainer="Mikkel Elle Lepperød",
      maintainer_email="m.e.lepperod@medisin.uio.no",
      long_description=long_description,
      url="https://github.com/CINPLA/phy-dev",
      platforms=['Linux', "Windows"],
      cmdclass=cmdclass,
      )
