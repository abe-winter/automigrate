#!/usr/bin/env python3
"entrypoint for automigrate command line"
# example:
# automig 218dd2c 'test/schema/*.sql' --initial
# automig 218dd2c...b5b40ce 'test/schema/*.sql'
# automig 218dd2c...HEAD 'test/schema/*.sql'

import argparse, git
from datetime import datetime
from .lib import ref_diff, githelp

PARSER = argparse.ArgumentParser(__doc__)
PARSER.add_argument('ref', help="single git ref (i.e. sha) or sha1...sha2")
PARSER.add_argument('glob', help="glob to grab paths, typicaly 'schema/*.sql' or something")
PARSER.add_argument('--initial', action='store_true', help="is this an initial commit (i.e. create metadata)")
PARSER.add_argument('--transactional', action='store_true', help="definitely enable this on DBs that support transactional DDL")

def main():
  args = PARSER.parse_args()
  if args.transactional:
    raise NotImplementedError('transactional DDL not supported yet')
  rev_tuple = githelp.parse_rev_to_tuple(args.ref)
  print(f'-- changeset created from {args} at {datetime.now()}')
  if args.initial:
    assert len(rev_tuple) == 1, "can't pass a sha range for --initial"
    raise NotImplementedError
  else:
    assert len(rev_tuple) == 2, "must pass a sha range or set --initial"
    changes = ref_diff.ref_range_diff(git.Repo(), *rev_tuple, args.glob)
    for sha, tables in changes.items():
      for table, stmts in tables.items():
        print(f'-- changes for {sha[:7]}.{table}')
        for stmt in stmts:
          print(stmt)

if __name__ == '__main__':
  main()
