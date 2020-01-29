"wrappers.py -- wrappers around sqlparse to get expression info"

import sqlparse

class MiscBadParse(Exception): pass

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
    ret = next((expr for expr in self.stmt if isinstance(expr, sqlparse.sql.Function)), None)
    if ret is None:
      raise MiscBadParse("Can't parse table declaration. Did you name a table with a sql keyword?", list(self.stmt))
    return ret

  @property
  def table(self):
    "return table name string"
    return self.decl().get_name()

def iswhitespace(token):
  "for splitting purposes, is this ignorable? includes whitespace & comments"
  # todo: do something else with comments, we probably want to decorate the parsed structure with special comments
  return token.is_whitespace or isinstance(token, sqlparse.sql.Comment)

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

class ParsedColumn:
  # todo: py 3.7 dataclass
  __slots__ = ('success', 'name', 'type', 'default', 'unique', 'not_null', 'pkey')
  # todo: rename type (but it's a risky refactor with inadequate test coverage on sa_harness)
  # pylint: disable=redefined-builtin, too-many-arguments
  def __init__(self, success, name=None, type=None, default=None, unique=None, not_null=None, pkey=False):
    self.success = success
    self.name = name
    self.type = type
    self.default = default
    self.unique = unique
    self.not_null = not_null
    self.pkey = pkey

  def __eq__(self, other):
    # todo: py 3.7 dataclass provides this automatically
    if not isinstance(other, self.__class__):
      return False
    return tuple(map(lambda slot: getattr(self, slot), self.__slots__)) == \
      tuple(map(lambda slot: getattr(other, slot), other.__slots__))

  def __repr__(self):
    return f"<{self.__class__.__name__} {' '.join(map(lambda slot: f'{slot}={getattr(self, slot)}', self.__slots__))}>"

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

  def parse(self):
    "return a ParsedColumn. This is rudimentary and will fail on hard cases"
    name, *tokens = self.tokens
    if not isinstance(name, sqlparse.sql.Identifier):
      return ParsedColumn(False)
    type_, *tokens = tokens
    if not isinstance(type_, sqlparse.sql.Function) and type_.ttype[-1] not in ('Builtin', 'Keyword'):
      return ParsedColumn(False)
    success = ParsedColumn(True, name.value, type_.value)
    if tokens and isinstance(tokens[0], sqlparse.sql.SquareBrackets):
      brackets, *tokens = tokens
      success.type += brackets.value
    while tokens:
      if tokens[0].ttype and tokens[0].ttype[-1] == 'Keyword':
        if tokens[0].normalized.lower() == 'default':
          _, val, *tokens = tokens
          success.default = val.value
        elif tokens[0].normalized.lower() == 'not null':
          _, *tokens = tokens
          success.not_null = True
        elif tokens[0].normalized.lower() == 'unique':
          _, *tokens = tokens
          success.unique = True
        elif tokens[0].normalized.lower() == 'primary':
          _, key, *tokens = tokens
          assert key.normalized.lower() == 'key'
          success.pkey = True
      else:
        return ParsedColumn(False)
    return success

def split_pun_paren(decl):
  """return things inside parenthesis, split by punctuation.
  decl is a 'function expression' i.e. a piece of a create table
  """
  paren = next(
    expr for expr in decl
    if isinstance(expr, sqlparse.sql.Parenthesis)
  )
  return split_pun(paren)


class CreateTable(WrappedStatement):
  def __init__(self, stmt):
    assert stmt.get_type() == 'CREATE'
    super().__init__(stmt)

  def groups(self):
    "helper for columns() and pkey_fields(). returns tokens inside the first paren, grouped by punctuation split."
    return split_pun_paren(self.decl())

  def columns(self):
    return [
      Column(group)
      for group in self.groups()
      # note: this guard blocks 'primary key (a,b)' kind of thing
      if isinstance(group[0], sqlparse.sql.Identifier)
    ]

  def pkey_fields(self):
    "return list of column names that are in primary key"
    for group in self.groups():
      if isinstance(group[0], sqlparse.sql.Token) and group[0].ttype and group[0].ttype[0] == 'Keyword' and group[0].value.lower() == 'primary':
        idents = [ident for ident, in split_pun_paren(group)]
        # note: in theory we just want identifiers, but there are a lot of tokens and people use them by accident to name columns; most SQL engines accept it
        # (and this parser can't handle ticks I don't think)
        assert all(isinstance(ident, (sqlparse.sql.Identifier, sqlparse.sql.Token)) for ident in idents)
        return [str(ident) for ident in idents]
    return [col.name for col in self.columns() if col.parse().pkey]

  @property
  def unique(self):
    "unique key -- in this case, ('create', name) because we only allow one create stmt per table"
    return ('create', self.table)

  def tail(self):
    "non-space tokens after column parens"
    paren_index = next((i for i, expr in enumerate(self.stmt) if isinstance(expr, sqlparse.sql.Function)), None)
    if paren_index is None:
      return None
    tail = self.stmt[paren_index + 1:]
    return [expr for expr in tail if not iswhitespace(expr) and expr.value != ';']

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

# pylint: disable=inconsistent-return-statements
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
