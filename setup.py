#!/usr/bin/env python3

import os
from distutils.core import setup
from setuptools import find_packages
from automig.version import __version__

setup(
  name='automig',
  version=__version__,
  description="Declarative, automatic db migrations using SQL & git as the source of truth",
  author="Abe Winter",
  author_email="awinter.public+automig@gmail.com",
  url="https://github.com/abe-winter/automigrate",
  packages=find_packages(include=['automig', 'automig.*']),
  entry_points = {
    'console_scripts': [
      'automig=automig.__main__:main',
      'automig_pg=automig.migrate_pg:main',
      'automig_sqlite=automig.automig_sqlite:main',
    ],
  },
  keywords=['sql', 'migration', 'git', 'diff'],
  install_requires=[
    'sqlparse==0.3.0',
    'gitpython==3.1.0',
    'pyyaml==5.1',
  ],
  extras_require={
    # postgres required for automig_pg script. if install fails, do `apt install libpq-dev`
    "postgres": ["psycopg2-binary==2.8.4"],
  },
  python_requires='>=3.6', # for format strings
  long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
  long_description_content_type='text/markdown',
)
