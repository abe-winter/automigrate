"ref_diff.py -- run sql diffs on git repos"

import sqlparse
from . import githelp, diffing

def files_to_smts(readables):
  "given a list of read()-ablel files, read them, parse them and return list of statements"
  stmts = []
  for readable in readables:
    stmts.extend(sqlparse.parse(readable.read()))
  return stmts

def ref_diff(repo, ref1, ref2, pattern):
  "given repo, refs & glob pattern, return list of uniquely identified statements making up diff (or uniquely ID'd errors)"
  contents = (
    githelp.get_streams(repo.commit(ref).tree, pattern)
    for ref in (ref1, ref2)
  )
  left, right = [
    files_to_smts(readables)
    for readables in contents
  ]
  return diffing.diff(left, right)
