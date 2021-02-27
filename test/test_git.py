import git, glob, pytest, sqlparse, os, collections
from automig.lib import githelp, ref_diff, diffing
from .test_diffing import ARGS

SHAS = {
  'create-t1': '2801578',
  'add-t1-col': '2ff9297cb26c9491c159af728ad6734ad06f8542',
  'add-t2-t1a': 'f8b1048fd12b6ef41568801867b67d3ca74904f3',
  'unsup-alter-col': 'c479bb0',
  'create-ext': '5cf2a621',
  'create-enum': '48fc5774',
  'modify-enum': '1a0ceab8',
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

def test_creat_ext():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['unsup-alter-col'], SHAS['create-ext'], GLOB)
  shadiff, = diff.values()
  # sorry: annoying that this has comments in here.
  # it happens because diffing.diff() passes through the raw stmt for new keys, and the parser attaches comments
  assert shadiff == {('ext', '"uuid-ossp"'): ['-- sql.sql\n-- example schema file with git history we rely on in tests\n\ncreate extension if not exists "uuid-ossp";']}

def test_create_enum():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['create-ext'], SHAS['create-enum'], GLOB)
  shadiff, = diff.values()
  assert shadiff == {('enum', 'letters'): ["create type letters as enum ('a', 'b');"]}

def test_modify_enum():
  diff = ref_diff.ref_range_diff(ARGS, git.Repo(), SHAS['create-enum'], SHAS['modify-enum'], GLOB)
  err = list(diff.values())[0]['enum', 'letters'][0]
  assert isinstance(err, diffing.UnsupportedChange) # ugh because these don't support == I think

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
