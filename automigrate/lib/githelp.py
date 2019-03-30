"githelp.py -- helpers for doing things on git"

import git, fnmatch, os, collections

def parse_rev_to_tuple(rev_string):
  if '...' in rev_string:
    left, _, right = rev_string.partition('...')
    return left, right
  elif '..' in rev_string:
    raise ValueError("we don't support two-dot strings -- use a three-dot")
  else:
    return rev_string,

def get_paths(tree, pattern, root=()):
  """given tree (a git tree at a desired ref) return list of paths matching pattern
  note: this matches paths that existed at the time of ref, including files that don't exist now and excluding ones that exist on disk but were missing at ref
  """
  found = []
  for item in tree:
    if isinstance(item, git.Blob):
      path = os.path.join(*root, item.name)
      if fnmatch.fnmatch(path, pattern):
        found.append(path)
    elif isinstance(item, git.Tree):
      found.extend(get_paths(item, pattern, root + (item.name,)))
    else:
      raise NotImplementedError("unexpected type in tree", item)
  return found

def get_streams(tree, pattern):
  """given ref (git sha or reference as string) and glob (glob pattern as string)
  return list of read()-ables for file contents
  todo: support repos you're not inside of
  """
  return [tree[path].data_stream for path in get_paths(tree, pattern)]
