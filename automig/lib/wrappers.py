"wrappers.py -- wrappers around sqlparse to get expression info"

import sqlparse

class WrappedStatement:
  "base class"
  __slots__ = ('stmt',)

  def __init__(self, stmt):
    assert isinstance(stmt, sqlparse.sql.Statement)
    self.stmt = stmt

  def __eq__(self, other):
    "yes this is the way adults compare parse trees"
    return str(self.stmt).strip() == str(other.stmt).strip()

  def decl(self):
    "helper to get the function element, i.e. the table declaration"
    return next(expr for expr in self.stmt if isinstance(expr, sqlparse.sql.Function))

  @property
  def table(self):
    "return table name string"
    return self.decl().get_name()

def iswhitespace(token):
  # todo: learn more about this -- Token.Text.Whitespace.Newline, should I be testing ttype[2]?
  return isinstance(token, sqlparse.sql.Token) \
    and token.ttype \
    and (token.ttype[-1] == 'Whitespace' or token.ttype[-1] == 'Newline')

def split_pun(tokens):
  """Takes a list of tokens and other stuff.
  Returns contiguous blocks of non-punctuation, i.e. list of lists.
  Recurses into IdentifierList which are inserted in insane places.
  Also strips whitespace tokens.
  """
  groups = [[]]
  for tok in tokens:
    if isinstance(tok, sqlparse.sql.Token) and tok.ttype and tok.ttype[0] == 'Punctuation':
      if groups[-1]: # i.e. if there's a non-empty group
        groups.append([])
    elif iswhitespace(tok):
      pass
    elif isinstance(tok, sqlparse.sql.IdentifierList):
      # this is insane
      inner = split_pun(tok)
      groups[-1].extend(inner[0])
      groups.extend(inner[1:])
      # note: intentionally not putting an empty list on the end. This is covered in test_diffing.py
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
    assert stmt.get_type() == 'CREATE'
    super().__init__(stmt)

  def columns(self):
    decl = self.decl()
    paren = next(
      expr for expr in self.decl()
      if isinstance(expr, sqlparse.sql.Parenthesis)
    )
    return list(map(Column, split_pun(paren)))

  @property
  def unique(self):
    "unique key -- in this case, ('create', name) because we only allow one create stmt per table"
    return ('create', self.table)

class CreateIndex(WrappedStatement):
  def __init__(self, stmt):
    assert stmt.get_type() == 'CREATE'
    super().__init__(stmt)

  @property
  def index_name(self):
    index_index = next(i for i, tok in enumerate(self.stmt) if tok.ttype and tok.ttype[-1] == 'Keyword' and tok.value == 'index')
    on_index = next(i for i, tok in enumerate(self.stmt) if tok.ttype and tok.ttype[-1] == 'Keyword' and tok.value == 'on')
    block = self.stmt[index_index:on_index]
    ident, = next(tok for tok in block if isinstance(tok, sqlparse.sql.Identifier))
    return ident.value

  @property
  def unique(self):
    "unique key -- in this case, ('create', name) because we only allow one create stmt per table"
    return ('index', self.index_name)

def wrap(stmt):
  assert isinstance(stmt, sqlparse.sql.Statement)
  if stmt.get_type() == 'CREATE':
    keywords = [tok.value for tok in stmt if tok.ttype and tok.ttype[-1] == 'Keyword']
    if 'table' in keywords:
      return CreateTable(stmt)
    elif 'index' in keywords:
      return CreateIndex(stmt)
  elif stmt.get_type() == 'UNKNOWN':
    pass # cross fingers this means whitespace
  else:
    raise NotImplementedError(stmt.get_type(), stmt)
