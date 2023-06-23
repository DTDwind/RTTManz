#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import find_packages, setup

setup(
    name="RTTManz",
    version="1.6.0",
    author="Yu-Sen Cheng (DTDwind)",
    description="A simple Python package for analyzing the necessary data in Speaker Diarization using oracle RTTM files and audio files.",
    keywords="analyze rttm",
    url="https://github.com/DTDwind/RTTManz",
    install_requires=[
        'numpy>=1.22.4',
        'argparse',
        'soundfile>=0.10.2',
        'pathlib',
        'tabulate>=0.9.0',
    ],
    dependency_links=[],
    license="Apache-2.0 License",
    packages=find_packages(),
    long_description_content_type="text/markdown",
)
