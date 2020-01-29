#!/usr/bin/env python3
"entrypoint for automigrate command line"
# example:
# automig 2801578 'test/schema/*.sql' --initial
# automig 2801578...f8b1048 'test/schema/*.sql'
# automig 2801578...HEAD 'test/schema/*.sql'

import argparse, os, pathlib
from datetime import datetime
import git, yaml
from .lib import ref_diff, githelp
from .version import __version__

def build_parser():
  parser = argparse.ArgumentParser(description=__doc__ + f" v{__version__}")
  parser.add_argument('ref', help="single git ref (i.e. sha) or sha1...sha2")
  parser.add_argument('glob', help="glob to grab paths, typicaly 'schema/*.sql' or something. use single-quotes so bash doesn't complete it")
  parser.add_argument('--initial', action='store_true', help="is this an initial commit (i.e. create metadata)")
  parser.add_argument('--update-meta', action='store_true', help="apply / update the preamble; this may only work with postgres")
  parser.add_argument('--opaque', action='store_true')
  return parser

# this creates the meta tables
PREAMBLE = """
-- meta_meta stores the meta version
create table if not exists automigrate_meta_meta (id serial primary key, meta_version int, applied timestamp default now());
insert into automigrate_meta_meta (meta_version) values (3);

-- meta stores the schema version
create table if not exists automigrate_meta (id serial primary key, sha text, applied timestamp default now(), fromsha text, opaque bool, automig_version text);
"""

POSTGRES_PREAMBLE = """
-- meta_meta stores the meta version
create table if not exists automigrate_meta_meta (id serial primary key, meta_version int);
alter table automigrate_meta_meta add column if not exists applied timestamp default now();
insert into automigrate_meta_meta (meta_version) values (3);

-- meta stores the schema version
create table if not exists automigrate_meta (id serial primary key, sha text, applied timestamp default now());
alter table automigrate_meta add column if not exists fromsha text;
alter table automigrate_meta add column if not exists opaque bool;
alter table automigrate_meta add column if not exists automig_version text;
"""

def main_inner(args):
  rev_tuple = githelp.parse_rev_to_tuple(args.ref)
  lines = []
  lines.append(f'-- changeset created from {args} at {datetime.now()}')
  shas = []
  manual_mig = {}
  if os.path.exists('.manualmig.yml'):
    # todo: read this from repo root, not cwd
    manual_mig = yaml.safe_load(open('.manualmig.yml'))['overrides']
  if args.initial:
    if args.opaque:
      raise ValueError("don't pass --opaque with --initial")
    shas.append(None)
    lines.append(PREAMBLE)
    commit = git.Repo(search_parent_directories=True).commit(rev_tuple[0])
    shas.append(commit.hexsha)
    tree = commit.tree
    assert len(rev_tuple) == 1, "can't pass a sha range for --initial"
    for contents in githelp.get_streams(tree, pathlib.Path.cwd() / pathlib.Path(args.glob)):
      lines.append(contents.decode())
  else:
    assert len(rev_tuple) == 2, "must pass a sha range or set --initial"
    # todo: look up rev_tuple[0] so this isn't a short sha or HEAD~1 or something
    shas.append(rev_tuple[0])
    changes = ref_diff.ref_range_diff(git.Repo(search_parent_directories=True), *rev_tuple, args.glob, opaque=args.opaque)
    errors = ref_diff.extract_errors(changes)
    if errors:
      # todo: this is wrong. manual_mig should override whether or not there are errors
      remaining = ref_diff.try_repair_errors(errors, manual_mig, changes)
      if remaining:
        raise ValueError('errors not overridden in .manualmig.yml', remaining)
    if args.update_meta:
      lines.append(POSTGRES_PREAMBLE)
    for sha, tables in changes.items():
      if not tables:
        continue
      shas.append(sha)
      for table, stmts in tables.items():
        lines.append(f'-- changes for {sha[:7]}.{table}')
        lines.extend(stmts)
  for sha1, sha2 in zip(shas[:-1], shas[1:]):
    # todo: hard w/out depending on a sql driver but do some kind of escaping here
    sha1 = f"'{sha1}'" if sha1 is not None else 'NULL'
    lines.append(f"insert into automigrate_meta (fromsha, sha, automig_version, opaque) values ({sha1}, '{sha2}', '{read_version()}', {['false', 'true'][args.opaque]});")
  return '\n'.join(lines)

def main():
  print((main_inner(build_parser().parse_args())))

if __name__ == '__main__': main()
