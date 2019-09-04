#!/usr/bin/env python3
"entrypoint for automigrate command line"
# example:
# automig 218dd2c 'test/schema/*.sql' --initial
# automig 218dd2c...b5b40ce 'test/schema/*.sql'
# automig 218dd2c...HEAD 'test/schema/*.sql'

import argparse, git, os, yaml
from datetime import datetime
from .lib import ref_diff, githelp

PARSER = argparse.ArgumentParser(__doc__)
PARSER.add_argument('ref', help="single git ref (i.e. sha) or sha1...sha2")
PARSER.add_argument('glob', help="glob to grab paths, typicaly 'schema/*.sql' or something. use quotes so bash doesn't complete it")
PARSER.add_argument('--initial', action='store_true', help="is this an initial commit (i.e. create metadata)")

# this creates the meta tables
PREAMBLE = """
-- meta_meta stores the meta version (obviously)
create table automigrate_meta_meta (id serial primary key, meta_version int);
insert into automigrate_meta_meta (meta_version) values (1);

-- meta stores the schema version
create table automigrate_meta (id serial primary key, sha text, applied timestamp default now());
"""

def main():
  args = PARSER.parse_args()
  rev_tuple = githelp.parse_rev_to_tuple(args.ref)
  print(f'-- changeset created from {args} at {datetime.now()}')
  shas = []
  manual_mig = {}
  if os.path.exists('.manualmig.yml'):
    manual_mig = yaml.safe_load(open('.manualmig.yml'))['overrides']
  if args.initial:
    print(PREAMBLE)
    commit = git.Repo().commit(rev_tuple[0])
    shas.append(commit.hexsha)
    tree = commit.tree
    assert len(rev_tuple) == 1, "can't pass a sha range for --initial"
    for stream in githelp.get_streams(tree, args.glob):
      print(stream.read().decode())
  else:
    assert len(rev_tuple) == 2, "must pass a sha range or set --initial"
    changes = ref_diff.ref_range_diff(git.Repo(), *rev_tuple, args.glob)
    errors = ref_diff.extract_errors(changes)
    if errors:
      remaining = ref_diff.try_repair_errors(errors, manual_mig, changes)
      if remaining:
        raise ValueError('errors not overridden in .manualmig.yml', remaining)
    for sha, tables in changes.items():
      shas.append(sha)
      for table, stmts in tables.items():
        print(f'-- changes for {sha[:7]}.{table}')
        for stmt in stmts:
          print(stmt)
  for sha in shas:
    # todo: hard w/out depending on a sql driver but do some kind of escaping here
    print(f"insert into automigrate_meta (sha) values ('{sha}');")

if __name__ == '__main__':
  main()
