"diffing.py -- sql-diffing"

import collections
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

def diff_column(table, colname, left, right):
  "return list of stmts to alter column, or UnsupportedChange if we're confused"
  if not left.success or not right.success:
    # todo: add details (column name and rendered old/new)
    return [UnsupportedChange(f"the column parser failed on new or old change for col {colname}")]
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
    constraint_name = f'{table}_{colname}_key' # warning: this is postgres-specific; support with docs and check target dialect
    if not left.unique and not right.unique:
      raise NotImplementedError("is this case default <-> explicit 'not unique'? is there such a thing?")
    elif left.unique and not right.unique:
      ret.append(f"alter table {table} drop constraint {constraint_name};")
    elif not left.unique and right.unique:
      ret.append(UnsupportedChange("can't add unique constraint, file a bug"))
    else:
      raise NotImplementedError("unexpected case in uniqueness permutations")
  if left.not_null != right.not_null:
    # note: I think the possible values here are (None | True), shouldn't ever be False
    # todo: refactor this to `null` and include null / not_null as sources
    # todo: this is assuming that 'not specified' is nullable -- link to DB docs supporting this and figure out the pkey case
    ret.append(f"{prefix} {'set' if right.not_null else 'drop'} not null;")
  return ret

# todo: refactor, this is too complicated
# pylint: disable=too-many-branches
def diff_stmt(args, left, right):
  "diff two WrappedStmt with same unique key. return list of statements to run."
  assert left.unique == right.unique
  table = left.table
  if isinstance(left, wrappers.CreateTable):
    left_cols = {col.name: col for col in left.columns()}
    right_cols = {col.name: col for col in right.columns()}
    added_cols = [k for k in right_cols if k not in left_cols]
    changes = [
      f'alter table {table} add column {right_cols[k].render()};'
      for k in added_cols
    ]
    changed = {
      k: (left_cols[k], right_cols[k])
      for k in right_cols
      if k in left_cols and left_cols[k] != right_cols[k]
    }
    if changed:
      for left_col, right_col in changed.values():
        changes.extend(diff_column(table, left_col.name, left_col.parse(), right_col.parse()))
    for k in left_cols:
      if k not in right_cols:
        edit = f'alter table {table} drop column {k};'
        if args.dialect == 'sqlite':
          changes.append(f"-- {edit} -- sqlite doesn't drop columns")
        else:
          changes.append(edit)
    if left.tail() != right.tail():
      change = ' '.join([expr.value for expr in left.tail() or right.tail()])
      changes.append(UnsupportedChange(f"can't modify table suffix: `{change}`"))
    if left.pkey_fields() != right.pkey_fields():
      # note: order matters here too; don't compare sets
      if left.pkey_fields():
        # this gets inserted at the beginning because need to drop constraint before dropping column
        changes.insert(0, f'alter table {table} drop constraint {table}_pkey;')
      new_pkey = ', '.join(right.pkey_fields())
      if new_pkey:
        # note: ParsedColumn.pkey means that this is inline pkey stmt, no need to add constraint
        if set(added_cols) >= set(right.pkey_fields()) and any(right_cols[k].parse().pkey for k in added_cols):
          pass # adding a pkey column will add the constraint
        else:
          changes.append(f'alter table {table} add primary key ({new_pkey});')
    return changes
  elif isinstance(left, wrappers.CreateIndex):
    return [
      f'drop index {left.index_name};',
      str(right.stmt)
    ]
  else:
    raise DiffError("unhandled type", type(left))

def diff_stmts(args, left, right):
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
      output.extend(diff_stmt(args, key_l[k], key_r[k]))
  return output

def diff(args, left, right):
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
      changes = diff_stmts(args, groups_l[key], stmts)
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
