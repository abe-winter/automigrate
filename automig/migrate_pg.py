#!/usr/bin/env python3
"migrate_pg.py -- . requires psycopg2, i.e. you should install with 'postgres' optional requirement"

import argparse, os
import psycopg2 # pylint: disable=import-error
from .__main__ import build_parser, main_inner

def init(args, connect=psycopg2.connect, dialect='postgres'):
  "body for `init` command"
	# eval "automig $TARGET $AUTOMIG_GLOB --initial" | psql $AUTOMIG_CON --single-transaction
  sql = main_inner(build_parser().parse_args([args.target, args.glob, '--initial', '--dialect', dialect]))
  print(sql)
  if args.preview:
    return
  con = connect(args.automig_con)
  if dialect == 'sqlite':
    con.cursor().executescript(sql)
  else:
    con.cursor().execute(sql)
  con.commit()

def update(args, connect=psycopg2.connect, dialect='postgres'):
  "body for `update` command"
  con = connect(args.automig_con)
  cur = con.cursor()
  cur.execute('select sha from automigrate_meta order by id desc limit 1')
  last_sha, = cur.fetchone()
  range_ = f"{last_sha}...{args.target}"
  print("range is", range_)
  pass_down_args = [range_, args.glob, '--dialect', dialect]
  if args.opaque:
    pass_down_args.append('--opaque')
  sql = main_inner(build_parser().parse_args(pass_down_args))
  print(sql)
  if args.preview:
    return
  empty = not any(not line.startswith('--') for line in sql.splitlines())
  if empty:
    print('update is empty, skipping')
  else:
    if dialect == 'sqlite':
      con.cursor().executescript(sql)
    else:
      con.cursor().execute(sql)
    con.commit()

def create_parser(doc):
  parser = argparse.ArgumentParser(description=doc)
  parser.add_argument('--target', default="HEAD", help="Target sha or git ref to migrate to / initialize with")
  parser.add_argument('--glob', default="schema/*.sql", help="Path glob, gets passed down to automig")
  parser.add_argument('--preview', action="store_true", help="Do a dry-run. Show what the change would be without applying it")
  parser.add_argument('--automig-con', default=os.environ.get('AUTOMIG_CON'), help="DB connection string. if missing, tries to get AUTOMIG_CON from env")
  sub = parser.add_subparsers(dest='command')
  sub.add_parser('init', help="initialize a schema at target, install meta tables if missing")
  cmd_update = sub.add_parser('update', help="Read latest commit from DB and update to target")
  cmd_update.add_argument('--opaque', action='store_true', help="Pass down to automig")
  return parser

def main():
  args = create_parser(__doc__).parse_args()
  assert args.automig_con, "pass --automig-con param or AUTOMIG_CON in env"
  if args.command == 'update':
    update(args)
  elif args.command == 'init':
    init(args)
  else:
    raise ValueError('unknown command', args.command)

if __name__ == '__main__': main()
