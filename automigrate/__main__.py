#!/usr/bin/env python3
"entrypoint for automigrate command line"

import argparse
from .lib import diffing

PARSER = argparse.ArgumentParser(__doc__)
PARSER.add_argument('git_diff', help="git sha or delta")
PARSER.add_argument('glob', help="glob to grab paths, typicaly 'schema/*.sql' or something")
PARSER.add_argument('--initial', action='store_true', help="is this an initial commit (i.e. create metadata)")
PARSER.add_argument('--transaction', action='store_true', help="definitely enable this on DBs that support transactional DDL") 

def main():
  args = PARSER.parse_args()
  print(args)
  raise NotImplementedError

if __name__ == '__main__':
  main()
