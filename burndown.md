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
* [ ] check that drop table / drop index works when removed from schema (and support some kind of placeholder to suppress deletion)
* [ ] Need a way to check live schema against desired to call out problems
* undo, i.e. what would be 'down' in a typical migration tool.
  - [ ] This may work out of the box (pass `HEAD...HEAD~1` instead of `HEAD~1...HEAD`), but needs tests
  - [ ] up/down sections in .manualmig.yml
* documentation for:
  - [ ] writing schema files
  - [ ] creating an initial migration
  - [ ] checklist for running migrations: determining last sha, inspecting migration, running migration (postgres / mysql)
  - [ ] resolving a rebase
  - [ ] troubleshoot and resolve `automigrate_meta` errors
  - [ ] using manualmig when the tool is confused
* [x] `--opaque` flag to repair non-linear git history (i.e. rebase)

## Burndown

* [ ] [0.2.0] enums
* [ ] [0.2.0] integration test with mysql and postgres
* [ ] [0.2.0] take more than one glob
* [ ] [0.2.0] test 'create extension' and support if not working
* [ ] [0.2.0] `.manualmig.yml` skip section for skipping bad migrations that need to be opaque
* [ ] [0.2.0] ensure capitalized keywords support in test suite
* [ ] [0.2.0] command to list dangerous operations in a diff (anything that drops data or schemas, any big / slow locking operations), so users can require CI signoff
* [ ] [0.2.0] design & test master-branch-only mode (because committing cross-branch migrations can cause trouble with squash commits)