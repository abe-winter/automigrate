import pytest, sqlparse
from automig.lib import diffing

CREATE_TABLE = [
  'create table t1 (a int);',
  'create table t1 (a int); create table t2 (a int);',
]

def test_create_table():
  delta = diffing.diff(*map(sqlparse.parse, CREATE_TABLE))
  assert delta == {'t2': ['create table t2 (a int);']}

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
  assert delta == {'t1': ['alter table t1 add column b int;']}

MODIFY_COLUMN = [
  'create table t1 (a int primary key, b int default 10, c text, d varchar(12));',
  # this is modifying a default, setting not nullable, and changing a varchar size
  'create table t1 (a int primary key, b int default 20, c text not null, d varchar(24));',
]

def test_modify_column():
  print(diffing.diff(*map(sqlparse.parse, MODIFY_COLUMN)))
  raise NotImplementedError

DROP_COLUMN = [
  'create table t1 (a int primary key, b int, c int);',
  'create table t1 (a int primary key, c int);',
]

def test_drop_column():
  delta = diffing.diff(*map(sqlparse.parse, DROP_COLUMN))
  assert delta == {'t1': ['alter table t1 drop column b;']}

@pytest.mark.skip
def test_modify_key():
  raise NotImplementedError

CREATE_INDEX = [
  'create unique index idx_col1 on t1 (col1);',
  'create unique index idx_col1 on t1 (col1); create unique index idx_col2 on t1 (col2);',
]

def test_add_index():
  delta = diffing.diff(*map(sqlparse.parse, CREATE_INDEX))
  assert delta == {'t1': ['create unique index idx_col2 on t1 (col2);']}

@pytest.mark.skip
def test_all_caps_keywords():
  raise NotImplementedError

NEWLINE = [
  'create table whatever (\n  a int\n);',
  'create table whatever (\n  a int,\n  b int\n);'
]

def test_newline():
  # this isn't asserting anything -- checking for a bug which caused a crash
  diffing.diff(*map(sqlparse.parse, NEWLINE))

COMMENT = [
  'create table whatever (\n  a int -- hello\n);',
  'create table whatever (\n  a int, -- hello\n  b int\n);'
]

def test_comments():
  # not asserting, just checking for crash
  diffing.diff(*map(sqlparse.parse, COMMENT))
