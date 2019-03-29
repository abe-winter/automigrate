"ref_diff.py -- run sql diffs on git repos"

import sqlparse
from . import githelp, diffing

def files_to_smts(readables):
  "given a list of read()-able files, read them, parse them and return list of statements"
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

def ref_range_diff(repo, ref1, ref2, pattern):
  "run ref_diff() once per intermediate commit for commits who change files matching pattern"
  commits = [repo.commit(ref1)] + list(repo.iter_commits(
    f'{ref1}...{ref2}',
    paths=pattern
  ))
  return {
    right.hexsha: ref_diff(repo, left.hexsha, right.hexsha, pattern)
    for left, right in zip(commits[:-1], commits[1:])
  }
