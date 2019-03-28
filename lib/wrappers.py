"wrappers.py -- wrappers around sqlparse to get expression info"

import sqlparse

class WrappedStatement:
  "base class"
  __slots__ = ('stmt',)

  def __eq__(self, other):
    "yes this is the way adults compare parse trees"
    return str(self.stmt).strip() == str(other.stmt).strip()

def split_pun(tokens):
  "helper -- takes a list of tokens and returns contiguous blocks of non-punctuation, i.e. list of lists. also strips whitespace tokens"
  groups = [[]]
  for tok in tokens:
    if isinstance(tok, sqlparse.sql.Token) and tok.ttype and tok.ttype[0] == 'Punctuation':
      if groups[-1]: # i.e. if there's a non-empty group
        groups.append([])
    elif isinstance(tok, sqlparse.sql.Token) and tok.ttype and tok.ttype[-1] == 'Whitespace':
      pass
    else:
      groups[-1].append(tok)
  if not groups[-1]:
    groups.pop()
  return groups

class Column:
  def __init__(self, tokens):
    self.tokens = tokens

  @property
  def name(self):
    assert isinstance(self.tokens[0], sqlparse.sql.Identifier)
    return self.tokens[0].value

  def __eq__(self, other):
    return [tok.value for tok in self.tokens] == [tok.value for tok in other.tokens]

  def render(self):
    return ' '.join(map(str, self.tokens))

class CreateTable(WrappedStatement):
  def __init__(self, stmt):
    assert isinstance(stmt, sqlparse.sql.Statement)
    assert stmt.get_type() == 'CREATE'
    self.stmt = stmt

  def decl(self):
    "helper to get the function element, i.e. the table declaration"
    return next(expr for expr in self.stmt if isinstance(expr, sqlparse.sql.Function))

  def columns(self):
    decl = self.decl()
    paren = next(
      expr for expr in self.decl()
      if isinstance(expr, sqlparse.sql.Parenthesis)
    )
    return list(map(Column, split_pun(paren)))

  @property
  def table(self):
    "return table name string"
    return self.decl().get_name()

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
