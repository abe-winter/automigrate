import git, glob, pytest
from automigrate.lib import githelp, ref_diff

SHAS = {
  'create-t1': '218dd2c',
  'add-t1-col': '9dcbd4e',
  'add-t2-t1a': 'b5b40ce',
  'unsup-alter-col': '0756d87',
}
GLOB ='test/schema/*.sql'

def test_get_paths():
  tree = git.Repo().commit(SHAS['create-t1']).tree
  assert githelp.get_paths(tree, GLOB) == ['test/schema/sql.sql']

@pytest.mark.skip
def test_create():
  repo = git.Repo()
  path, = glob.glob(GLOB)
  blob = repo.commit(SHAS['create-t1']).tree[path]
  print(blob.data_stream.read())
  print(dir(blob))
  raise NotImplementedError

def test_addcol():
  repo = git.Repo()
  diff = ref_diff.ref_range_diff(git.Repo(), SHAS['create-t1'], SHAS['add-t1-col'], GLOB)
  print('diff', diff)
  raise NotImplementedError

@pytest.mark.skip
def test_add_multi_commit():
  raise NotImplementedError

@pytest.mark.skip
def test_addtable():
  raise NotImplementedError

@pytest.mark.skip
def test_unsup():
  raise NotImplementedError
