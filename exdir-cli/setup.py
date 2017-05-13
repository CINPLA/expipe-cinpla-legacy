# -*- coding: utf-8 -*-
from setuptools import setup
import os
import subprocess
from setuptools import setup, find_packages

long_description = open("README.md").read()

setup(
    name="exdir-cli",
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        exdir=exdircli.main:main
    '''
)
