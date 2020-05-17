import pytest, sqlparse, collections, re
from automig.lib import diffing, wrappers

RE_KEYWORDS = re.compile('create|table|int|primary key|alter|add|column|set|default|not null|type|varchar|unique|index|drop|constraint|partition|by|on|range')

ARGS = collections.namedtuple('args', 'dialect')('postgres')

def diff_parse(stmts):
  "wrapper helper"
  return diffing.diff(ARGS, *map(sqlparse.parse, stmts))

def case_keywords(raw, casefn):
  "helper for case manipulation. ugh. this is necessary because 'alter table' stmts are always lowercase"
  found = RE_KEYWORDS.findall(raw)
  for keyword in found:
    raw = raw.replace(keyword, casefn(keyword))
  return raw

def tolower(vals):
  if isinstance(vals, list):
    return [tolower(val) for val in vals]
  elif isinstance(vals, dict):
    return {key.lower(): tolower(val) for key, val in vals.items()}
  return case_keywords(vals, str.lower)

def toupper(vals):
  if isinstance(vals, list):
    return [toupper(val) for val in vals]
  elif isinstance(vals, dict):
    return {key: toupper(val) for key, val in vals.items()}
  return case_keywords(vals, str.upper)

@pytest.fixture(params=[tolower, toupper])
def tocase(request):
  return request.param

CREATE_TABLE = [
  'create table t1 (a int);',
  'create table t1 (a int); create table t2 (a int);',
]

def test_case_keywords():
  assert case_keywords(CREATE_TABLE[0], str.upper) == 'CREATE TABLE t1 (a INT);'

def test_create_table(tocase):
  delta = diff_parse(tocase(CREATE_TABLE))
  assert delta == tocase({'t2': ['create table t2 (a int);']})

@pytest.mark.skip
def test_drop_table():
  "tests that removed tables *aren't* dropped -- there's like no reason to right?"
  raise NotImplementedError

ADD_COLUMN = [
  'create table t1 (a int primary key);',
  'create table t1 (a int primary key, b int);',
]

def test_add_column(tocase):
  delta = diff_parse(tocase(ADD_COLUMN))
  assert delta == {'t1': [f'alter table t1 add column b {tocase("int")};']}

ADD_COLUMN_PKEY = [
  'create table t1 (b int);',
  'create table t1 (a int primary key, b int);',
]

def test_add_column_pkey(tocase):
  "this is testing that this doesn't also do an 'alter table add primary key'"
  assert diff_parse(tocase(ADD_COLUMN_PKEY))['t1'] == \
    [f'alter table t1 add column a {tocase("int primary key")};']

MODIFY_COLUMN = [
  'create table t1 (a jsonb primary key, b int default 10, c text[], d varchar(12));',
  # this is modifying a default, setting not nullable, and changing a varchar size
  # the array column is to test Column.parse() on array types
  # the jsonb column is because jsonb is a keyword not a builtin, broke the parser initially
  'create table t1 (a jsonb primary key, b int default 20, c text[] not null, d varchar(24));',
]

def test_modify_column(tocase):
  assert diff_parse(tocase(MODIFY_COLUMN)) == {'t1': [
    'alter table t1 alter column b set default 20;',
    'alter table t1 alter column c set not null;',
    f'alter table t1 alter column d type {tocase("varchar")}(24);',
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
  # make sure it doesn't treat 'primary key' as a column
  assert [col.name for col in wrappers.wrap(sqlparse.parse("create table t1 (a int, b int, primary key (a,b))")[0]).columns()] == ['a', 'b']

def test_pkey_fields(tocase):
  assert ['a'] == wrappers.wrap(sqlparse.parse("create table t1 (a int primary key, b int)")[0]).pkey_fields()
  assert ['a', 'b'] == wrappers.wrap(sqlparse.parse("create table t1 (a int, b int, primary key (a,b))")[0]).pkey_fields()

DROP_COLUMN = [
  'create table t1 (a int primary key, b int, c int);',
  'create table t1 (a int primary key, c int);',
]

def test_drop_column(tocase):
  delta = diff_parse(tocase(DROP_COLUMN))
  assert delta == {'t1': ['alter table t1 drop column b;']}

DROP_COLUMN_PKEY = [
  'create table t1 (a int primary key, b int);',
  'create table t1 (b int);',
]

def test_drop_column_pkey(tocase):
  "this is testing that the 'drop constraint' comes before the 'drop column'"
  assert diff_parse(tocase(DROP_COLUMN_PKEY))['t1'] == \
    ['alter table t1 drop constraint t1_pkey;', 'alter table t1 drop column a;']

MODIFY_KEY_1 = [
  'create table t1 (a int primary key);',
  'create table t1 (a int, primary key (a));',
]

MODIFY_KEY_2 = [
  'create table t1 (a int primary key);',
  'create table t1 (a int, b int, primary key (a, b));',
]

MODIFY_KEY_3 = [
  'create table t1 (a int primary key);',
  'create table t1 (a int);',
]

def test_modify_key(tocase):
  assert not diff_parse(tocase(MODIFY_KEY_1))
  assert diff_parse(tocase(MODIFY_KEY_2))['t1'] == [
    'alter table t1 drop constraint t1_pkey;',
    f'alter table t1 add column b {tocase("int")};',
    'alter table t1 add primary key (a, b);',
  ]
  assert diff_parse(MODIFY_KEY_3)['t1'] == ['alter table t1 drop constraint t1_pkey;']
  assert diff_parse(reversed(MODIFY_KEY_3))['t1'] == ['alter table t1 add primary key (a);',]

CREATE_INDEX = [
  'create unique index idx_col1 on t1 (col1);',
  'create unique index idx_col1 on t1 (col1); create unique index idx_col2 on t1 (col2);',
]

def test_add_index(tocase):
  delta = diff_parse(tocase(CREATE_INDEX))
  assert delta == tocase({'t1': ['create unique index idx_col2 on t1 (col2);']})

EDIT_INDEX = [
  'create index idx_col1 on t1 (col1);',
  'create index idx_col1 on t1 (col1, col2);',
]

def test_no_index_name(tocase):
  # nobody should be using unnamed indexes with automig, the tool doesn't know the created name, but this is testing for a crash
  wrapped = wrappers.wrap(sqlparse.parse(tocase('create index on t1 (a);'))[0])
  assert wrapped.index_name is None

def test_edit_index(tocase):
  assert diff_parse(tocase(EDIT_INDEX))['t1'] == [
    'drop index idx_col1;',
    tocase('create index idx_col1 on t1 (col1, col2);'),
  ]

@pytest.mark.skip
def test_all_caps_keywords():
  raise NotImplementedError

NEWLINE = [
  'create table whatever (\n  a int\n);',
  'create table whatever (\n  a int,\n  b int\n);',
]

def test_newline(tocase):
  # this isn't asserting anything -- checking for a bug which caused a crash
  diff_parse(tocase(NEWLINE))

COMMENT = [
  'create table whatever (\n  a int -- hello\n);',
  'create table whatever (\n  a int, -- hello\n  b int\n);',
]

def test_comments(tocase):
  # not asserting, just checking for crash
  diff_parse(tocase(COMMENT))

PARTITION = [
  'create table whatever (a boolean primary key);',
  'create table whatever (a boolean primary key) partition by range (a);',
]

def test_tail(tocase):
  "directly test CreateTable.tail()"
  no, yes = [wrappers.wrap(parsed[0]) for parsed in map(sqlparse.parse, tocase(PARTITION))]
  assert no.tail() == []
  assert tocase('partition by range (a)') == ' '.join(map(str, yes.tail()))

def test_partition(tocase):
  assert diff_parse(tocase(PARTITION))['whatever'][0].args == \
    (f"can't modify table suffix: `{tocase('partition by range (a)')}`",)

UNIQUE = [
  'create table whatever (a text unique);',
  'create table whatever (a text);',
]

def test_modify_unique(tocase):
  assert diff_parse(tocase(UNIQUE))['whatever'] == ['alter table whatever drop constraint whatever_a_key;']
  assert diff_parse(reversed(tocase(UNIQUE)))['whatever'][0].args == ("can't add unique constraint, file a bug",)
