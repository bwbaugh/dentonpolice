#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import setuptools


setuptools.setup(
    name='dentonpolice',
    author='Wesley Baugh',
    author_email='wesley@bwbaugh.com',
    url='https://github.com/bwbaugh/dentonpolice',
    license=(
        'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 '
        'Unported License'
    ),
    packages=setuptools.find_packages(exclude=['tests']),
    setup_requires=['setuptools'],
    # These are the packages that are explicitly depend on.
    # On the other hand, the packages in `requirements.txt` include
    # all implicit dependencies i.e., the packages required by the
    # packages that the service depends on.
    install_requires=[
        'PyYAML>=3.11',
        'boto>=2.38.0',
        'raven>=5.2.0',
        'twython>=3.1.2',
    ],
)
