"diffing.py -- sql-diffing"

import collections, sqlparse
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
      print('changed', {k: (a.render(), b.render()) for k, (a, b) in changed.items()})
      raise NotImplementedError('changed columns')
    if any(k not in right_cols for k in left_cols):
      raise NotImplementedError('dropped cols')
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
      output.append(key_r[k].stmt)
    elif key_l[k] == key_r[k]:
      pass # not relevant to diff
    else:
      output.extend(diff_stmt(key_l[k], key_r[k]))
  return output

def diff(left, right):
  """take two lists of statements.
  return a list of statements to migrate from left to right.
  throw an error? (or list of explanatory errors) if we can't gen a migration.
  """
  # todo: figure out some way to store stmt order
  groups_l = group_by_table(map(wrappers.wrap, left))
  groups_r = group_by_table(map(wrappers.wrap, right))
  output = collections.OrderedDict()
  for key, stmts in groups_r.items():
    if key in groups_l:
      changes = [str(stmt).strip() for stmt in diff_stmts(groups_l[key], stmts)]
      if changes:
        output[key] = changes
    else:
      output[key] = [str(wrapped.stmt).strip() for wrapped in stmts]
  return output
