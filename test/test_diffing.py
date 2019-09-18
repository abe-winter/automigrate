import pytest, sqlparse
from automig.lib import diffing, wrappers

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
  'create table t1 (a jsonb primary key, b int default 10, c text[], d varchar(12));',
  # this is modifying a default, setting not nullable, and changing a varchar size
  # the array column is to test Column.parse() on array types
  # the jsonb column is because jsonb is a keyword not a builtin, broke the parser initially
  'create table t1 (a jsonb primary key, b int default 20, c text[] not null, d varchar(24));',
]

def test_modify_column():
  assert diffing.diff(*map(sqlparse.parse, MODIFY_COLUMN)) == {'t1': [
    'alter table t1 alter column b set default 20;',
    'alter table t1 alter column c set not null;',
    'alter table t1 alter column d type varchar(24);',
  ]}

@pytest.mark.skip
def test_diff_column():
  "directly test diff_column cases"
  raise NotImplementedError

def parse_column(type_):
  stmt, = sqlparse.parse(f"create table t1 (x {type_})")
  col, = wrappers.wrap(stmt).columns()
  return col.parse()

def test_column_parser():
  "directly test wrappers.Column.parse() cases"
  for type_ in ['int', 'jsonb', 'text', 'varchar(12)', 'int[]', 'text[]']:
    assert parse_column(type_) == wrappers.ParsedColumn(True, 'x', type_)
    assert parse_column(type_ + ' not null') == wrappers.ParsedColumn(True, 'x', type_, not_null=True)
    assert parse_column(type_ + ' unique') == wrappers.ParsedColumn(True, 'x', type_, unique=True)
    assert parse_column(type_ + ' default now()') == wrappers.ParsedColumn(True, 'x', type_, default='now()')
    assert parse_column(type_ + ' default 20') == wrappers.ParsedColumn(True, 'x', type_, default='20')
    assert parse_column(type_ + " default 'hello'") == wrappers.ParsedColumn(True, 'x', type_, default="'hello'")
    assert parse_column(type_ + ' not null unique default 20') == wrappers.ParsedColumn(True, 'x', type_, not_null=True, unique=True, default='20')

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
