#!/usr/bin/env python3

from distutils.core import setup

setup(
  name='automig',
  version='0.0.1',
  description="Command to diff SQL schemas in git and apply the migrations",
  author="Abe Winter",
  url="https://github.com/abe-winter/automigrate",
  packages=['automig'],
  entry_points = {
    'console_scripts': ['automig=automig.__main__:main'],
  },
  keywords=['sql', 'migration', 'git', 'diff'],
  install_requires=[
    'sqlparse==0.3.0',
    'gitpython==2.1.11',
    'pyyaml==5.1',
  ],
  python_requires='>=3.6', # for format strings
)
