import pytest, sqlparse
from automig.lib import sa_harness, wrappers

def args(classic=True):
  argv = ['schema.sql']
  if classic:
    argv.append('--classic')
  return sa_harness.PARSER.parse_args(argv)

def transform_string(args, string):
  "helper"
  return sa_harness.transform(args, map(wrappers.wrap, sqlparse.parse(string)))

def test_read_globs():
  argv = args()
  "this one is just exercising"
  stmts = sa_harness.read_glob_stmts('test/schema/*.sql')

CASES = {
  'simple': 'create table t1 (a int);',
  'pkey': 'create table t1 (a int primary key, b int);',
  'default': 'create table t1 (a timestamp default now());',
  'index': 'create index i1 on t1(a);',
  'composite': 'create table t1 (a int, b int, primary key (a, b));',
  'enum': "create type letters as enum ('a', 'b');\ncreate table t (col letters);",
}

def test_transform_simple_classic():
  argv = args()
  assert transform_string(argv, CASES['simple']) == \
    ["t1_table = sa.Table('t1', META,\n  sa.Column('a', sa.Integer),\n)"]
  # primary key
  assert transform_string(argv, CASES['pkey']) == \
    ["t1_table = sa.Table('t1', META,\n  sa.Column('a', sa.Integer, primary_key=True),\n  sa.Column('b', sa.Integer),\n)"]
  # default
  assert transform_string(argv, CASES['default']) == \
    ["t1_table = sa.Table('t1', META,\n  sa.Column('a', sa.DateTime, server_default=sa.text('now()')),\n)"]

def test_transform_simple_decl():
  argv = args(False)
  assert transform_string(argv, CASES['simple']) == \
    ["class T1(Base):\n  __tablename__ = 't1'\n  a = sa.Column(sa.Integer)"]
  # primary key
  assert transform_string(argv, CASES['pkey']) == \
    ["class T1(Base):\n  __tablename__ = 't1'\n  a = sa.Column(sa.Integer, primary_key=True)\n  b = sa.Column(sa.Integer)"]
  # default
  assert transform_string(argv, CASES['default']) == \
    ["class T1(Base):\n  __tablename__ = 't1'\n  a = sa.Column(sa.DateTime, server_default=sa.text('now()'))"]

def test_transform_index():
  argv = args()
  assert transform_string(argv, CASES['index']) == \
    ["i1_index = sa.Index('i1', t1_table.c.a)"]

def test_transform_composite_key_classic():
  argv = args()
  assert transform_string(argv, CASES['composite']) == \
    ["t1_table = sa.Table('t1', META,\n  sa.Column('a', sa.Integer, primary_key=True),\n  sa.Column('b', sa.Integer, primary_key=True),\n)"]

def test_transform_composite_key_decl():
  argv = args(False)
  assert transform_string(argv, CASES['composite']) == \
    ["class T1(Base):\n  __tablename__ = 't1'\n  a = sa.Column(sa.Integer, primary_key=True)\n  b = sa.Column(sa.Integer, primary_key=True)"]

def test_transform_enum_classic():
  argv = args()
  assert transform_string(argv, CASES['enum']) == [
    'class lettersEnum(enum.Enum):\n  a = 1\n  b = 2',
    "t_table = sa.Table('t', META,\n  sa.Column('col', sa.Enum(lettersEnum)),\n)",
  ]

def test_transform_enum_decl():
  argv = args(False)
  assert transform_string(argv, CASES['enum']) == [
    'class lettersEnum(enum.Enum):\n  a = 1\n  b = 2',
    "class T(Base):\n  __tablename__ = 't'\n  col = sa.Column(sa.Enum(lettersEnum))",
  ]
