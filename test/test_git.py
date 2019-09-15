import git, glob, pytest, sqlparse
from automig.lib import githelp, ref_diff, diffing

SHAS = {
  'create-t1': '218dd2c',
  'add-t1-col': '9dcbd4e81e9a0dd7629ed7ae82a86891a88f76f3',
  'add-t2-t1a': 'b5b40ce718ea7241fee8d0a3826f244d21bf413c',
  'unsup-alter-col': '0756d87',
}
GLOB ='test/schema/*.sql'

def test_get_paths():
  tree = git.Repo().commit(SHAS['create-t1']).tree
  assert githelp.get_paths(tree, GLOB) == ['test/schema/sql.sql']

@pytest.mark.skip
def test_create():
  diff = ref_diff.ref_range_diff(git.Repo(), SHAS['create-t1'], SHAS['add-t1-col'], GLOB)
  print('diff', diff)
  raise NotImplementedError

def test_addcol():
  diff = ref_diff.ref_range_diff(git.Repo(), SHAS['create-t1'], SHAS['add-t1-col'], GLOB)
  assert diff == {
    SHAS['add-t1-col']: {'t1': ['alter table t1 add column b int;']},
  }

def test_add_multi_commit():
  diff = ref_diff.ref_range_diff(git.Repo(), SHAS['create-t1'], SHAS['add-t2-t1a'], GLOB)
  assert diff == {
    SHAS['add-t1-col']: {
      't1': ['alter table t1 add column b int;'],
    },
    SHAS['add-t2-t1a']: {
      't1': ['create index t1a on t1 (a);'],
      't2': ['create table t2 (a int primary key);'],
    },
  }

MOD_COLUMN = [
  'create table t1 (a int primary key, b int);',
  'create table t1 (a int primary key, b int unique);',
]

def test_error_bubbling():
  sha_table_stmts = {'sha': diffing.diff(*map(sqlparse.parse, MOD_COLUMN))}
  errors = ref_diff.extract_errors(sha_table_stmts)
  manual = {'sha': {'t1': ['hello']}}
  remaining = ref_diff.try_repair_errors(errors, manual, sha_table_stmts)
  assert not remaining
  assert sha_table_stmts['sha']['t1'] == ['hello']
