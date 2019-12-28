# automig changelog

## 0.0.x

* 0.0.17 feature: changing named index drops & re-adds it
* 0.0.16 1ab5ec9 bugfix: --initial mode wasn't reading the glob (abs paths for globs broke this)
* 0.0.15 12a79e8
  - bugfix: fix order of drop/add constraint in some modify key cases
  - feature: support dropping unique constraint on a column
  - bugfix: fix case where primary key parser gets tricked by other keywords at the end of the create table statement
* 0.0.14 3d846fa feature: add, drop and change primary key
* 0.0.13 b861ea0 bugfix: throw an error when 'partition by' changes rather than incorrect empty diff
* 0.0.12 4d43251 bugfix: support separate `primary key ()` tuple in `create table`
* 0.0.11 6c4b8e9 feature: --opaque flag for resolving messy git histories
* 0.0.10 b2b707c
  - bugfix: permit invocations outside repo root; fix in 0.0.5 fixed the crash but didn't make glob relative
  - near-breaking change: automigrate_meta new columns, you have to pass --update-meta the first time this runs or do `automig HEAD...HEAD . --update-meta`
  - version bump: automigrate_meta_meta version 3
* 0.0.9 4f95864 bugfix: support jsonb and array types in alter parser
* 0.0.8 7e782ba feature: drop & alter column
* 0.0.7 72cecac bugfix: --initial was broken by streams fix in 0.0.3
* 0.0.6 6c40716 bugfix: ignore comments
* 0.0.5 e66fc1e bugfix: `search_parent_directories` so you don't have to run from repo root
* 0.0.4 4de552e bugfix: 0.0.3 didn't bundle VERSION file correctly, crashed on load
* 0.0.3 532c021
	- bugfix: `data_stream` property in gitpython throws funky traceback when created from more than one blob & then read; so read stream proactively
	- BROKEN, do not use
* 0.0.2 53149ef bugfix: treat newlines correctly as whitespace in create table stmts
* 0.0.1 3a3bfd0 initial release
