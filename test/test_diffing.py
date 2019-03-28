import pytest, sqlparse

from ..lib import diffing

CREATE_TABLE = [
  'create table t1 (a int);',
  'create table t1 (a int); create table t2 (a int);',
]

def test_create_table():
  delta = diffing.diff(*map(sqlparse.parse, CREATE_TABLE))
  assert list(map(str, delta)) == ['create table t2 (a int);']

DROP_TABLE = []

@pytest.mark.skip
def test_drop_table():
  "tests that removed tables *aren't* dropped -- there's like no reason to right?"
  raise NotImplementedError

@pytest.mark.skip
def test_add_column():
  raise NotImplementedError

@pytest.mark.skip
def test_modify_column():
  raise NotImplementedError

@pytest.mark.skip
def test_add_index():
  raise NotImplementedError
