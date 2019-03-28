import pytest, sqlparse

from ..lib import diffing

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
  'create table t1 (a int);',
  'create table t1 (a int, b int);',
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
  '',
  'create unique index idx_name on table (col);',
]

def test_add_index():
  raise NotImplementedError
