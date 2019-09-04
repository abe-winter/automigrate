#!/usr/bin/env python3

from distutils.core import setup

setup(
  name='automig',
  version='0.0.1',
  description="Command to diff SQL schemas in git and apply the migrations",
  author="Abe Winter",
  url="https://github.com/abe-winter/automigrate",
  packages=['automigrate'],
  entry_points = {
    'console_scripts': ['automig=automigrate.__main__:main'],
  },
  keywords=['sql', 'migration', 'git', 'diff'],
)
