import pytest, sqlparse
from automigrate.lib import diffing

CREATE_TABLE = [
  'create table t1 (a int);',
  'create table t1 (a int); create table t2 (a int);',
]

def test_create_table():
  delta = diffing.diff(*map(sqlparse.parse, CREATE_TABLE))
  assert list(map(str, delta)) == ['create table t2 (a int);']

@pytest.mark.skip
def test_drop_table():
  "tests that removed tables *aren't* dropped -- there's like no reason to right?"
  raise NotImplementedError

ADD_COLUMN = [
  'create table t1 (a int primary key);',
  'create table t1 (a int primary key, b int);',
]

def test_add_column():
  delta = diffing.diff(*map(sqlparse.parse, ADD_COLUMN))
  assert delta == ['alter table t1 add column b int;']

@pytest.mark.skip
def test_modify_column():
  raise NotImplementedError

@pytest.mark.skip
def test_modify_key():
  raise NotImplementedError

CREATE_INDEX = [
  'create unique index idx_col1 on t1 (col1);',
  'create unique index idx_col1 on t1 (col1); create unique index idx_col2 on t1 (col2);',
]

def test_add_index():
  delta = diffing.diff(*map(sqlparse.parse, CREATE_INDEX))
  print('delta', str(delta[0]))
  assert list(map(str, delta)) == ['create unique index idx_col2 on t1 (col2);']

@pytest.mark.skip
def test_all_caps_keywords():
  raise NotImplementedError
