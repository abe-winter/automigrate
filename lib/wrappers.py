"wrappers.py -- wrappers around sqlparse to get expression info"

import sqlparse

class WrappedStatement:
  "base class"
  __slots__ = ('stmt',)

  def __eq__(self, other):
    "yes this is the way adults compare parse trees"
    return str(self.stmt).strip() == str(other.stmt).strip()

class CreateTable(WrappedStatement):
  def __init__(self, stmt):
    assert isinstance(stmt, sqlparse.sql.Statement)
    assert stmt.get_type() == 'CREATE'
    self.stmt = stmt

  @property
  def table(self):
    "return table name string"
    decl = next(expr for expr in self.stmt if isinstance(expr, sqlparse.sql.Function))
    return decl.get_name()

  @property
  def unique(self):
    "unique key -- in this case, ('create', name) because we only allow one create stmt per table"
    return ('create', self.table)

def wrap(stmt):
  assert isinstance(stmt, sqlparse.sql.Statement)
  if stmt.get_type() == 'CREATE':
    return CreateTable(stmt)
  else:
    raise NotImplementedError(stmt.get_type())
