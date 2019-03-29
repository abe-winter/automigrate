#!/usr/bin/env python3

from distutils.core import setup

setup(
  name='automigrate',
  version='0.0.1',
  description="",
  author="Abe Winter",
  url="https://github.com/abe-winter/automigrate",
  packages=['automigrate'],
  entry_points = {
    'console_scripts': ['automig=automigrate.__main__:main'],
  }
)
