"sa_harness.py -- create sqlalchemy definitions from create table & index stmts"

import sqlparse, glob, collections
from . import wrappers, diffing

def read_glob_stmts(glob_pattern):
  "return wrapped stmts for files matching glob"
  stmts = []
  for fname in glob.glob(glob_pattern):
    stmts.extend(map(wrappers.wrap, sqlparse.parse(open(fname).read())))
  return stmts

def column_args(column):
  "parse sql column in a horrible way and "
  state = 'name'
  dets = {}
  pkey = None
  for tok in map(str, column.tokens):
    if tok in ('collate', 'constraint', 'check', 'not', 'null'):
      raise ValueError('unsupported token', tok)
    if state == 'name':
      if tok == 'primary':
        paren = column.tokens[-1]
        assert isinstance(paren, sqlparse.sql.Parenthesis)
        return None, None, None, [str(ident) for ident, in wrappers.split_pun(paren)]
      dets['name'] = tok
      state = 'type'
    elif state == 'type':
      dets['type'] = tok
      state = 'dets'
    elif state == 'dets':
      if tok == 'primary':
        dets['primary_key'] = True
        state = 'pkey'
      elif tok == 'default':
        state = 'default'
      else:
        raise ValueError('unhandled token in back section', tok)
    elif state == 'pkey':
      assert tok == 'key'
      state = 'dets'
    elif state == 'default':
      dets['server_default'] = "sa.text('%s')" % tok
      state = 'dets'
  return dets.pop('name'), dets.pop('type'), dets, None

TYPES = {
  'int': 'Integer',
  'jsonb': 'JSONB',
  'json': 'JSON',
  'text': 'Text',
  'uuid': 'UUID',
  'timestamp': 'DateTime',
}

def render_col(col_name, col_type, details, composite_pkey):
  if composite_pkey and col_name in composite_pkey:
    details['primary_key'] = True
  return f"sa.Column('{col_name}', sa.{TYPES[col_type]}{', ' + ', '.join('%s=%s' % pair for pair in details.items()) if details else ''})"

def transform(table_stmts, delim=', \n'):
  "return some representation of sqlalchemy tables"
  table_strings = []
  for tablename, stmts in diffing.group_by_table(table_stmts).items():
    indexes = []
    table = None
    cols = collections.OrderedDict()
    composite_pkey = None
    for stmt in stmts:
      if isinstance(stmt, wrappers.CreateTable):
        for col in stmt.columns():
          name, type_, dets, pkey = column_args(col)
          if pkey:
            composite_pkey = pkey
          else:
            cols[name, type_] = dets
      elif isinstance(stmt, wrappers.CreateIndex):
        print('index', stmt.index_name, stmt.decl())
        raise NotImplementedError
      else:
        raise TypeError('unhandled statement type', type(stmt))
    col_strings = [
      render_col(col_name, col_type, details, composite_pkey)
      for (col_name, col_type), details in cols.items()
    ]
    table_strings.append(f"sa.Table('{tablename}', META{delim}{delim.join(col_strings)})")
  return table_strings
