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
  assert sa_tables == ["t1_table = sa.Table('t1', META, sa.Column('a', sa.Integer))"]
  # primary key
  sa_tables = transform_string('create table t1 (a int primary key, b int);')
  assert sa_tables == ["t1_table = sa.Table('t1', META, sa.Column('a', sa.Integer, primary_key=True), sa.Column('b', sa.Integer))"]
  # default
  sa_tables = transform_string('create table t1 (a timestamp default now());')
  assert sa_tables == ["t1_table = sa.Table('t1', META, sa.Column('a', sa.DateTime, server_default=sa.text('now()')))"]

def test_transform_index():
  sa_tables = transform_string('create index i1 on t1(a);')
  assert sa_tables == ["i1_index = sa.Index('i1', t1_table.c.a)"]

def test_transform_composite_key():
  # note: I think that still doesn't support this
  sa_tables = transform_string('create table t1 (a int, b int, primary key (a, b));')
  assert sa_tables == ["t1_table = sa.Table('t1', META, sa.Column('a', sa.Integer, primary_key=True), sa.Column('b', sa.Integer, primary_key=True))"]
