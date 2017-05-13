# -*- coding: utf-8 -*-
from setuptools import setup
import os
import subprocess
from setuptools import setup, find_packages

setup(
    name="expipe-cli",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'expipe=expipecli.main:expipe'
        ],
    }
)
