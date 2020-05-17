import git, glob, pytest, sqlparse, os
from automig.lib import githelp, ref_diff, diffing
from .test_diffing import ARGS

SHAS = {
  'create-t1': '2801578',
  'add-t1-col': '2ff9297cb26c9491c159af728ad6734ad06f8542',
  'add-t2-t1a': 'f8b1048fd12b6ef41568801867b67d3ca74904f3',
  'unsup-alter-col': 'c479bb0',
}
GLOB ='test/schema/*.sql'

def test_get_paths():
  repo = git.Repo()
  tree = repo.commit(SHAS['create-t1']).tree
  assert githelp.get_paths(tree, os.path.join(repo.working_dir, GLOB)) == ['test/schema/sql.sql']

@pytest.mark.skip
def test_create():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['create-t1'], SHAS['add-t1-col'], GLOB)
  raise NotImplementedError

def test_addcol():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['create-t1'], SHAS['add-t1-col'], GLOB)
  assert diff == {
    SHAS['add-t1-col']: {'t1': ['alter table t1 add column b int;']},
  }

def test_add_multi_commit():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['create-t1'], SHAS['add-t2-t1a'], GLOB)
  assert diff == {
    SHAS['add-t1-col']: {
      't1': ['alter table t1 add column b int;'],
    },
    SHAS['add-t2-t1a']: {
      't1': ['create index t1a on t1 (a);'],
      't2': ['create table t2 (a int primary key);'],
    },
  }

def test_add_multi_commit_opaque():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['create-t1'], SHAS['add-t2-t1a'], GLOB, opaque=True)
  assert diff == {SHAS['add-t2-t1a']: {
    't1': ['alter table t1 add column b int;', 'create index t1a on t1 (a);'],
    't2': ['create table t2 (a int primary key);'],
  }}

MOD_COLUMN = [
  'create table t1 (a int primary key, b int);',
  'create table t1 (a int primary key, b int unique);',
]

def test_error_bubbling():
  sha_table_stmts = {'sha': diffing.diff(ARGS, *map(sqlparse.parse, MOD_COLUMN))}
  errors = ref_diff.extract_errors(sha_table_stmts)
  manual = {'sha': {'t1': ['hello']}}
  remaining = ref_diff.try_repair_errors(errors, manual, sha_table_stmts)
  assert not remaining
  assert sha_table_stmts['sha']['t1'] == ['hello']
