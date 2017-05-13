# -*- coding: utf-8 -*-
from setuptools import setup
import os
import subprocess
from setuptools import setup, find_packages

long_description = open("README.md").read()

subprocess.run(['pyrcc5', '-o', 'exdirbrowser/qml_qrc.py',
                'exdirbrowser/qml.qrc'])

setup(
    name="Exdir Browser",
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        exdir-browser=exdirbrowser.main:main
    '''
)
