# -*- coding: utf-8 -*-
from setuptools import setup
import os
import subprocess
from setuptools import setup, find_packages

long_description = open("README.md").read()

subprocess.run(['pyrcc5', '-o', 'expipebrowser/qml_qrc.py',
                'expipebrowser/qml.qrc'])

setup(
    name="expipe-browser",
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        expipe-browser=expipebrowser.main:main
    '''
)
