## What does & doesn't work

* [x] Adding tables, indexes and columns should mostly work
* [x] drop column works
* [x] modifying columns partially works, supports changes to types, defaults, nullable. Read the `diff_column()` function for up-to-date information and file bugs for specific holes.
* [x] add, drop and change primary keys
* [x] For diffs that are erroring, you can override with a [.manualmig.yml file](./.manualmig.yml)
* [ ] not sure if postgres 'partition by' is supported but the differ will become very upset if you change it
* [ ] Be careful with using unescaped keywords as names (i.e. a table named table) -- you'll likely confuse the parser even where your sql engine allows it
* [ ] This hasn't been tested on a wide range of syntax (i.e. arrays / json)
* [ ] Not sure if capitalized SQL keywords are supported (todo add tests)
* undo, i.e. what would be 'down' in a typical migration tool.
  - [ ] This may work out of the box (pass `HEAD...HEAD~1` instead of `HEAD~1...HEAD`), but needs tests
  - [ ] up/down sections in .manualmig.yml
* documentation for (THIS IS TOP PRIORITY AFTER 0.1):
  - [ ] writing schema files
  - [ ] creating an initial migration
  - [ ] checklist for running migrations: determining last sha, inspecting migration, running migration (postgres / mysql)
  - [ ] resolving a rebase
  - [ ] troubleshoot and resolve `automigrate_meta` errors
  - [ ] using manualmig when the tool is confused
* [x] `--opaque` flag to repair non-linear git history (i.e. rebase)
* [ ] foreign keys

## Burndown

### 0.1.1 (sqlite)

* [x] automig\_sqlite command
* [x] basic integration test for automig\_pg
* [ ] run some of the schema transformations on a sqlite db in test

### 0.1.x

* [ ] instructions for working with branches locally + in prod
* [ ] keep glob string in history; changing glob should be an intentional thing, not an accident. glob should only be in `init`, reuse in update
* [ ] before / after for alter column -- a lot of code may depend on column order
* .manualmig.yml:
	- [ ] hooks for data migrations
	- [x] 'opaque' set for skipping bad migrations that need to be opaque
* [ ] confirm sqlite is in transaction
* [ ] add --init-if-necessary flag to 'update' (will be different per DB) so there can be a single entrypoint command
* working dir features
	- [ ] warn when schema.sql has uncommitted changes
	- [ ] way to do a test run on working dir w/ rollback (rollback tricky because of missing 'drop table' in all dialects and lack of 'drop column' sup in sqlite)
* [ ] 'pre' and 'post' migrations -- i.e. add columns before deploying backend code, drop columns after (potentially using a timer to support rollback)
* [x] update deps, in particular sqlparse and gitpython

### 0.2.0

* enums
	- [x] create
	- [ ] modify
* [ ] take more than one glob, or better: list of globs so I don't have to single-quote asterisks
* [x] test 'create extension' and support if not working
* [ ] command to list dangerous operations in a diff (anything that drops data or schemas, any big / slow locking operations), so users can require CI signoff
* parsing features
	- [ ] consider switching parsers, or writing one -- we currently wrap sqlparse pretty intensely
	- [ ] fix random keywords not allowed as column names (or at least warn). `source`, `owner`. write a failing test for this.

### 0.3.0

* [ ] integration test with postgres, maybe also mysql
* [ ] design drop table
* [ ] .manualmig.yml feature to rename table and column
* [ ] advanced merging support -- some way to inherit columns from other libraries / locations

### 0.4.0

* [ ] foreign key support
