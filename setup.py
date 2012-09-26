#!/usr/bin/env python
from setuptools import setup

setup(
    name = "thirdlight",
    version = "0.1.0",
    author = "ReThought Ltd",
    author_email = "code@rethought-solutions.com",
    url = "https://github.com/Rethought/thirdlight.git",

    package_dir = {'':'src'},
    py_modules = ['thirdlight'],
    install_requires = ['requests'],
    license = "BSD",
    keywords = "imaging, asset_management, thirdlight, api",
    description = "Python API library for the ThirdLight image management system",
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
