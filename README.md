# automigrate

Tool to diff SQL schemas in git and apply the migrations.

Use this if you don't like to manage migrations separately from your declarative schema definitions.

* [Warning this is beta software](#beta-software)
* [Features](#features)
* [Installation & basic use](#installation--basic-use)
* [What does & doesn't work](#what-does--doesnt-work)
* [Comparison vs other tools](#comparison-vs-other-tools)
* [Using with ORMs](#using-with-orms)

## Beta software

This is beta software and you should be careful with its output.

* Eyeball the migrations before applying them
* Proactively raise github issues for things that seem broken

## Features

* Operates on `*.sql` files (i.e. files with `create table` and `create index` statements)
* Operates on git -- meaning that it tracks the git version of applied migration and can create a SQL migration given two git refs
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

## What does & doesn't work

* [x] Adding tables, indexes and columns should mostly work
* [ ] modifying primary keys doesn't work
* [ ] modifying column types doesn't work (even something inoccuous like a default)
* [x] For diffs that are erroring, you can override with a [.manualmig.yml file](./.manualmig.yml)
* [ ] Be careful with using unescaped keywords as names (i.e. a table named table) -- you'll likely confuse the parser even where your sql engine allows it
* [ ] This hasn't been tested on a wide range of syntax (i.e. arrays / json)
* [ ] Not sure if capitalized SQL keywords are supported (todo add tests)
* [ ] Arbitrary whitespace changes can probably confuse the parser (todo add tests)
* [ ] Need a way to check live schema against desired to call out problems
* undo, i.e. what would be 'down' in a typical migration tool.
	- [ ] This may work out of the box (pass `HEAD...HEAD~1` instead of `HEAD~1...HEAD`), but needs tests
	- [ ] up/down sections in .manualmig.yml
* documentation for:
	- [ ] writing schema files
	- [ ] creating an initial migration
	- [ ] checklist for running migrations: determining last sha, inspecting migration, running migration (postgres / mysql)
	- [ ] resolving a rebase
	- [ ] using manualmig when the tool is confused
* [ ] add tool version to migrations table
* [ ] design CI integration
* [ ] open design question: any reason to support non-DDL statements? what would this be used for?
* [ ] Anything that messes with the git history (like a rebase) is deeply confusing to this tool and will result in bad migrations. Workaround:
    - **warning**: this method only works if the rebase doesn't change migrations
    - figure out the new sha that corresponds to your last old sha -- most likely you can do a `git show $OLDSHA` and then look for that commit msg in `git log`
    - and insert that corresponding sha into the `automigrate_meta` table: `psql -h 172.17.0.2 -U postgres -c "insert into automigrate (sha) values ('$NEWSHA')"`
    - you should be good to go
    - todo: find a way to automatically detect & recover from rebases
    - todo: provide an `--opaque` argument that doesn't try to create granular changes for each commit in the history
* [ ] include `from_sha` in `automigrate_meta` table for audit trail

## Comparison vs other tools

* alembic / other auto migration generators
	- they're generally language-specific and ORM-specific, this isn't
	- they're not git-aware so you need to manage migration files
	- they can usually connect to your DB -- this is designed to be run directly as SQL
* apex sql diff
	- they can operate on 'script folders' and integrate with source control
	- not sure what this means in practice
	- I think this product is GUI-first and only runs on windows?
* sqlite sqldiff.exe
	- seems like a really good tool if you're operating on sqlite databases
* liquibase
	- supports 4 formats for migration (xml, yml, json, sql) -- this supports 0 because it doesn't need them
	- requires you to explictly define migrations (I think) -- this doesn't

## Using with ORMs

Your ORM has to be willing to import a schema from create table statements. (I don't know any ORM that does this out of the box, although some can reflect a live DB, like [sqlalchemy's automap](https://docs.sqlalchemy.org/en/latest/orm/extensions/automap.html)).

This repo contains a barebones, mostly untested harness to [generate sqlalchemy models from create table statements](./automig/lib/sa_harness.py). You can run it with:

```bash
python -m automig.lib.sa_harness 'test/schema/*.sql'
```

Happy to accept PRs to generate ORM defs from `create table` stmts (or vice versa).

## Development workflow

```bash
# enable .envrc with `direnv allow` if necessary, or set up your own virtualenv
# pip install -r requirements.txt
pip install pytest
pytest # in repo root
```

If you want to pitch in on the project, there are a bunch of `@pytest.mark.skip` tests that need to be filled in (most require feature development to get them passing).
