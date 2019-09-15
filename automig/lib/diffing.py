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

def diff_column(table, left, right):
  "return list of stmts to alter column, or UnsupportedChange if we're confused"
  if not left.success or not right.success:
    # todo: add details (column name and rendered old/new)
    return [UnsupportedChange("the column parser failed on an alter")]
  assert left.name == right.name
  ret = []
  prefix = f"alter table {table} alter column {left.name}"
  if left.type != right.type:
    ret.append(f"{prefix} type {right.type};")
  if left.default != right.default:
    if right.default is None:
      ret.append(UnsupportedChange("can't unset default, file a bug and workaround by setting `default null` for now"))
    else:
      ret.append(f"{prefix} set default {right.default};")
  if left.unique != right.unique:
    ret.append(UnsupportedChange("can't modify uniqueness, file a bug"))
  if left.not_null != right.not_null:
    # note: I think the possible values here are (None | True), shouldn't ever be False
    # todo: refactor this to `null` and include null / not_null as sources
    # todo: this is assuming that 'not specified' is nullable -- link to DB docs supporting this and figure out the pkey case
    ret.append(f"{prefix} {'set' if right.not_null else 'drop'} not null;")
  return ret

def diff_stmt(left, right):
  "diff two WrappedStmt with same unique key. return list of statements to run."
  assert left.unique == right.unique
  table = left.table
  if isinstance(left, wrappers.CreateTable):
    left_cols = {col.name: col for col in left.columns()}
    right_cols = {col.name: col for col in right.columns()}
    changes = [
      f'alter table {table} add column {right_cols[k].render()};'
      for k in right_cols if k not in left_cols
    ]
    changed = {
      k: (left_cols[k], right_cols[k])
      for k in right_cols
      if k in left_cols and left_cols[k] != right_cols[k]
    }
    if changed:
      for left_col, right_col in changed.values():
        changes.extend(diff_column(table, left_col.parse(), right_col.parse()))
    for k in left_cols:
      if k not in right_cols:
        changes.append(f'alter table {table} drop column {k};')
    return changes
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
