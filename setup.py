#!/usr/bin/env python3

import os
from distutils.core import setup
from setuptools import find_packages

setup(
  name='automig',
  version=open(os.path.join(os.path.dirname(__file__), 'automig', 'VERSION')).read().strip(),
  description="Declarative, automatic db migrations using SQL & git as the source of truth",
  author="Abe Winter",
  url="https://github.com/abe-winter/automigrate",
  packages=find_packages(include=['automig', 'automig.*']),
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
  long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
  long_description_content_type='text/markdown',
  include_package_data=True,
)
