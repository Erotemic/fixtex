#!/usr/bin/env python2.7
"""
pip install git+https://github.com/Erotemic/fixtex.git
"""
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='fixtex',
    version='1.0',
    author='Jon Crall',
    url='https://github.com/Erotemic/fixtex',
    license='Apache 2',
    packages=['fixtex'],
    install_requires=[
        'bibtexparser',
    ],
    entry_points={
        'console_scripts': [
            # Register specific python functions as command line scripts
            'fixbib=fixtex.fix_bib:main',
            'fixtex=fixtex.fix_tex:main'
        ],
    }
)
