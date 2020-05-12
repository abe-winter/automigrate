#!/usr/bin/env python3
"automig_sqlite.py -- entrypoint for sqlite migrations"

import sqlite3
from .migrate_pg import create_parser, init, update

def main():
  args = create_parser(__doc__).parse_args()
  if args.command == 'update':
    update(args, sqlite3.connect)
  elif args.command == 'init':
    init(args, sqlite3.connect)
  else:
    raise ValueError('unknown command', args.command)

if __name__ == '__main__': main()
