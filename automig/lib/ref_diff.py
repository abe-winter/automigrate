"ref_diff.py -- run sql diffs on git repos"

import sqlparse, collections, os, pathlib
from . import githelp, diffing

def files_to_smts(fulltexts):
  "given a list of file contents, read them, parse them and return list of statements"
  stmts = []
  for text in fulltexts:
    stmts.extend(sqlparse.parse(text))
  return stmts

def ref_diff(repo, ref1, ref2, pattern):
  "given repo, refs & glob pattern, return list of uniquely identified statements making up diff (or uniquely ID'd errors)"
  contents = (
    githelp.get_streams(repo.commit(ref).tree, pattern)
    for ref in (ref1, ref2)
  )
  left, right = [
    files_to_smts(fulltexts)
    for fulltexts in contents
  ]
  return diffing.diff(left, right)

def ref_range_diff(repo, ref1, ref2, pattern, opaque=False):
  "run ref_diff() once per intermediate commit for commits who change files matching pattern"
  assert not os.path.isabs(pattern), "we don't know how to transform glob to absolute path -- file a bug"
  assert os.path.isabs(repo.working_dir), "working dir is non-abs -- file a bug"
  # note: pathlib '/' operator should filter out single-dot
  absglob = pathlib.Path.cwd() / pathlib.Path(pattern)
  assert not any(part == '.' or part == '..' for part in pathlib.Path(absglob).parts), "parent paths not supported -- file a bug"
  commits = list(repo.iter_commits(
    f'{ref1}...{ref2}',
    paths=str(absglob)
  ))
  if opaque:
    # note: this is intended to be len=0 when change list is empty
    commits = [repo.commit(ref1)] + commits[:1]
  else:
    commits.append(repo.commit(ref1))
    commits = list(reversed(commits))
  return collections.OrderedDict([
    [right.hexsha, ref_diff(repo, left.hexsha, right.hexsha, str(absglob))]
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
