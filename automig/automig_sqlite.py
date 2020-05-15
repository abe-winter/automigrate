#!/usr/bin/env python3
"automig_sqlite.py -- entrypoint for sqlite migrations"

import sqlite3
from .migrate_pg import create_parser, init, update

def main():
  args = create_parser(__doc__).parse_args()
  assert args.automig_con, "pass --automig-con param or AUTOMIG_CON in env"
  if args.command == 'update':
    update(args, connect=sqlite3.connect, dialect='sqlite')
  elif args.command == 'init':
    init(args, connect=sqlite3.connect, dialect='sqlite')
  else:
    raise ValueError('unknown command', args.command)

if __name__ == '__main__': main()
