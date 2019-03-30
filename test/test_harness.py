import pytest, sqlparse
from automigrate.lib import sa_harness, wrappers

def transform_string(string):
  "helper"
  return sa_harness.transform(map(wrappers.wrap, sqlparse.parse(string)), delim=', ')

def test_read_globs():
  "this one is just exercising"
  stmts = sa_harness.read_glob_stmts('test/schema/*.sql')

def test_transform_simple():
  sa_tables = transform_string('create table t1 (a int);')
  assert sa_tables == ["sa.Table('t1', META, sa.Column('a', sa.Integer))"]
  # primary key
  sa_tables = transform_string('create table t1 (a int primary key, b int);')
  assert sa_tables == ["sa.Table('t1', META, sa.Column('a', sa.Integer, primary_key=True), sa.Column('b', sa.Integer))"]
  # default
  sa_tables = transform_string('create table t1 (a timestamp default now());')
  assert sa_tables == ["sa.Table('t1', META, sa.Column('a', sa.DateTime, server_default=sa.text('now()')))"]

@pytest.mark.skip
def test_transform_index():
  raise NotImplementedError

@pytest.mark.skip
def test_transform_composite_key():
  raise NotImplementedError
