"ref_diff.py -- run sql diffs on git repos"

import sqlparse, collections
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
  commits = list(repo.iter_commits(
    f'{ref1}...{ref2}',
    paths=pattern
  ))
  commits.append(repo.commit(ref1))
  commits = list(reversed(commits))
  return collections.OrderedDict([
    [right.hexsha, ref_diff(repo, left.hexsha, right.hexsha, pattern)]
    for left, right in zip(commits[:-1], commits[1:])
  ])

def extract_errors(sha_table_stmts):
  ret = {
    sha: diffing.get_errors(table_stmts)
    for sha, table_stmts in sha_table_stmts.items()
  }
  for k, v in list(ret.items()):
    if not v:
      del ret[k]
  return ret

def try_repair_errors(errors, manual_overrides, sha_table_stmts):
  """Try to repair this.
  errors is {sha: {table: error_list}}
  manual_overrides is {sha: {table: stmts}}
  sha_table_stmts is {sha: {table: stmts}}
  returns remaining_errors, mutates sha_table_stmts.
  """
  for sha, table_errors in errors.items():
    for table in table_errors:
      if sha in manual_overrides and table in manual_overrides[sha]:
        sha_table_stmts[sha][table] = manual_overrides[sha][table]
  return extract_errors(sha_table_stmts)
