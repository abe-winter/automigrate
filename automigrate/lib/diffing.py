"diffing.py -- sql-diffing"

import collections, sqlparse, yaml
from . import wrappers

class DiffError(Exception): pass

def group_by_table(stmts):
  "take list of WrappedStatement"
  groups = collections.defaultdict(list)
  for stmt in stmts:
    if isinstance(stmt, (wrappers.CreateTable, wrappers.CreateIndex)):
      groups[stmt.table].append(stmt)
    elif stmt is None:
      pass # where are these coming from? it happens in the test suite even
    else:
      raise DiffError("unhandled type", type(stmt))
  return groups

class UnsupportedChange(Exception):
  "returned in place of a migration string when there's an error"

def diff_stmt(left, right):
  "diff two WrappedStmt with same unique key. return list of statements to run."
  assert left.unique == right.unique
  table = left.table
  if isinstance(left, wrappers.CreateTable):
    left_cols = {col.name: col for col in left.columns()}
    right_cols = {col.name: col for col in right.columns()}
    new_cols = [
      f'alter table {table} add column {right_cols[k].render()};'
      for k in right_cols if k not in left_cols
    ]
    changed = {
      k: (left_cols[k], right_cols[k])
      for k in right_cols
      if k in left_cols and left_cols[k] != right_cols[k]
    }
    if changed:
      detail = {k: (a.render(), b.render()) for k, (a, b) in changed.items()}
      return [UnsupportedChange("we don't know how to change columns", detail)]
    if any(k not in right_cols for k in left_cols):
      return [UnsupportedChange("we don't know how to drop columns")]
    return new_cols
  else:
    raise DiffError("unhandled type", type(left))

def diff_stmts(left, right):
  "takes WrappedStmt lists, all for same table, and compares them"
  key_l = {stmt.unique: stmt for stmt in left}
  key_r = {stmt.unique: stmt for stmt in right}
  output = []
  for k in key_r:
    if k not in key_l:
      output.append(str(key_r[k].stmt).strip())
    elif key_l[k] == key_r[k]:
      pass # not relevant to diff
    else:
      output.extend(diff_stmt(key_l[k], key_r[k]))
  return output

def diff(left, right):
  """take two lists of statements.
  return dict of {tablename: list of migration statements or errors}
  """
  # todo: figure out some way to apply statements in order even across tables
  # realistically this needs to be a database, not a nested dict -- it gets queried in a lot of ways
  groups_l = group_by_table(map(wrappers.wrap, left))
  groups_r = group_by_table(map(wrappers.wrap, right))
  output = collections.OrderedDict()
  for key, stmts in groups_r.items():
    if key in groups_l:
      changes = [stmt for stmt in diff_stmts(groups_l[key], stmts)]
      if changes:
        output[key] = changes
    else:
      output[key] = [str(wrapped.stmt).strip() for wrapped in stmts]
  return output

def get_errors(table_stmt_dict):
  return {
    table: [stmt for stmt in stmts if isinstance(stmt, Exception)]
    for table, stmts in table_stmt_dict.items()
    if any(isinstance(stmt, Exception) for stmt in stmts)
  }
