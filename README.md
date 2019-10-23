# automigrate

Tool to diff SQL schemas in git and apply the migrations.

Use this if you don't like to manage migrations separately from your declarative schema definitions.

* [Warning this is beta software](#beta-software)
* [Features](#features)
* [Installation & basic use](#installation--basic-use)
* [What's happening under the covers](#whats-happening-under-the-covers)
* [What does & doesn't work](#what-does--doesnt-work)
* [Comparison vs other tools](#comparison-vs-other-tools)
* [Using with ORMs](#using-with-orms)
* [Integrating with CI](#integrating-with-ci)

## Beta software

This is beta software and you should be careful with its output.

* Eyeball the migrations before applying them
* Proactively raise github issues for things that seem broken

## Features

* Operates on `*.sql` files (i.e. files with `create table` and `create index` statements)
* Operates on git -- meaning that it tracks the git version of applied migration and can create a SQL migration given two git refs
* Outputs migrations as SQL
* No need to write or store migrations for simple cases -- they're defined bidirectionally in terms of your git history
* Ability to specify migrations manually when needed
* Stores the history of applied migrations in sql in `automigrate_meta` table

## Philosophy

* Defining your schema in your ORM is nuts because it ties you to one language, reduces clarity, and sometimes limits SQL features you can use
* Existing migration tools don't pull their weight
* SQL is a more general skill than ORMs and other tools should therefore mirror SQL
* Mirroring live databases to get a schema is insane because are you tunneling to prod to run your linter? Live DB shouldn't be available to developers. Source of truth should be git.
* Schema should be versioned using the same git shas as code so the logic is easy to detect if a deploy requires a migration

## Installation & basic use

To install, `pip install automig` (or use `pip3` if that fails). This should install dependencies and register the automig command.

You can fall back to `git+https://github.com/abe-winter/automigrate` if you want latest master.

Typical invocations:

```bash
# create an initial migration (also create meta tables)
automig 218dd2c 'test/schema/*.sql' --initial | psql -h 172.17.0.2 -U postgres --single-transaction

# migrate a database
LAST_SHA=$(psql -h 172.17.0.2 -U postgres -t -c "select sha from automigrate_meta order by id desc limit 1")
echo migrating from $LAST_SHA
automig $LAST_SHA...b5b40ce 'test/schema/*.sql' | psql -h 172.17.0.2 -U postgres --single-transaction

# I guess you can just migrate to HEAD if you're feeling lucky
automig $LAST_SHA...HEAD 'test/schema/*.sql' | psql -h 172.17.0.2 -U postgres --single-transaction
```

## What's happening under the covers

Nothing fancy. When you run `automig 218dd2c...b5b40ce 'test/schema/*.sql'` (these are real SHAs in this git repo and will work if you clone the repo), it outputs:

```sql
-- changeset created from Namespace(glob='test/schema/*.sql', initial=False, opaque=False, ref='218dd2c...b5b40ce', update_meta=False) at 2019-09-26 01:57:58.404722
-- changes for 9dcbd4e.t1
alter table t1 add column b int;
-- changes for b5b40ce.t1
create index t1a on t1 (a);
-- changes for b5b40ce.t2
create table t2 (a int primary key);
insert into automigrate_meta (fromsha, sha, automig_version, opaque) values ('218dd2c', '9dcbd4e81e9a0dd7629ed7ae82a86891a88f76f3', '0.0.10', false);
insert into automigrate_meta (fromsha, sha, automig_version, opaque) values ('9dcbd4e81e9a0dd7629ed7ae82a86891a88f76f3', 'b5b40ce718ea7241fee8d0a3826f244d21bf413c', '0.0.10', false);
```

## What does & doesn't work

* [x] Adding tables, indexes and columns should mostly work
* [x] drop column works
* [x] modifying columns partially works, supports changes to types, defaults, nullable. Read the `diff_column()` function for up-to-date information and file bugs for specific holes.
* [ ] modifying primary keys doesn't work
* [x] For diffs that are erroring, you can override with a [.manualmig.yml file](./.manualmig.yml)
* [ ] not sure if postgres 'partition by' is supported but the differ will become very upset if you change it
* [ ] Be careful with using unescaped keywords as names (i.e. a table named table) -- you'll likely confuse the parser even where your sql engine allows it
* [ ] This hasn't been tested on a wide range of syntax (i.e. arrays / json)
* [ ] Not sure if capitalized SQL keywords are supported (todo add tests)
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

* [ ] [0.2.0] integration test with mysql and postgres
* [ ] [0.2.0] take more than one glob
* [ ] [0.2.0] support 'create extension'
* [ ] [0.2.0] support enums

## Comparison vs other tools

* [prisma lift](https://github.com/prisma/lift) has a declarative schema which *isn't* sql but looks kind of like it, and depends on a runtime DB to generate the migration diff, but seems like a neat tool
* [alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html), as far as I can tell, requires you to generate a skeleton python file for each change then fill it in yourself
* [sqlite sqldiff.exe](https://www.sqlite.org/sqldiff.html) can diff schemas but operates on full sqlite databases and I'm not sure if it outputs DDL
* liquibase might have a [diffing system](https://www.liquibase.org/documentation/diff.html) but from the docs it looks like it's outputting XML. And [they advise you not to use it](http://www.liquibase.org/2007/06/the-problem-with-database-diffs.html)
* [redgate sql compare](https://documentation.red-gate.com/sc/sql-server-management-studio-add-in/getting-started-with-the-add-in) seems to support comparing 'create table' schemas across git versions, although it looks like you have to find the SHAs by hand in a GUI
* [migra](https://github.com/djrobstep/migra) seems to require two live DBs to run a diff (one with current schema, one with new)
* [sqitch](https://sqitch.org) seems to require manually specifying `deploy` sql (and optionally `revert` & `verify`)

## Using with ORMs

Your ORM has to be willing to import a schema from create table statements. (I don't know any ORM that does this out of the box, although some can reflect a live DB, like [sqlalchemy's automap](https://docs.sqlalchemy.org/en/latest/orm/extensions/automap.html)).

This repo contains a barebones, mostly untested harness to [generate sqlalchemy models from create table statements](./automig/lib/sa_harness.py). You can run it with:

```bash
python -m automig.lib.sa_harness 'test/schema/*.sql'
```

Happy to accept PRs to generate ORM defs from `create table` stmts (or vice versa).

## Integrating with CI

This is how I would apply migrations in CI if I had a few weeks off to build tooling. If you try this & it works, let me know.

* Flag the migration in your code review tool before merging the change to master
  - Ideally the CR tool would run automig against master branch and show automig's output so the reviewer can sign off
  - [terraform's version of this](https://www.terraform.io/docs/github-actions/index.html) is not a bad template to borrow
* Detect that a migration needs to be applied when deploying
  - This means that your deploy bot needs to have access to your prod DB
  - For continuous automatic deployment setups, you may want to block auto deploy for and require explicit signoff for deploys which require a migration
  - Alert / page in the appropriate place when a deploy is held because it has a migration
* Apply the migration from deploy CI
  - To be safe, this requires an exactly-once semantic
  - Unlock the automatic deployment when the migration has successfully applied
  - Alert / page on error applying
  - Some migrations may require downtime for part or all of your cluster -- these migrations probably won't be automatic
  - Note that the order of new code & migration depends on the contents of the migration. [This staffjoy post](https://blog.staffjoy.com/dont-migrate-databases-automatically-5039ab061365?gi=3451f6178158#5822) points out that with ORMs that select all columns, `add column` & `drop column` can both be done with 0 downtime, but drop column migrations must be applied **after** the new code is out

## Development workflow

```bash
# enable .envrc with `direnv allow` if necessary, or set up your own virtualenv
# pip install -r requirements.txt
pip install pytest
pytest # in repo root
```

If you want to pitch in on the project, there are a bunch of `@pytest.mark.skip` tests that need to be filled in (most require feature development to get them passing).
