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
-- changeset created from Namespace(glob='test/schema/*.sql', initial=False, ref='218dd2c...b5b40ce') at 2019-09-14 22:15:55.421146
-- changes for 9dcbd4e.t1
alter table t1 add column b int;
-- changes for b5b40ce.t1
create index t1a on t1 (a);
-- changes for b5b40ce.t2
create table t2 (a int primary key);
insert into automigrate_meta (sha) values ('9dcbd4e81e9a0dd7629ed7ae82a86891a88f76f3');
insert into automigrate_meta (sha) values ('b5b40ce718ea7241fee8d0a3826f244d21bf413c');
```

## What does & doesn't work

* [x] Adding tables, indexes and columns should mostly work
* [x] drop column works
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
* [ ] I think you have to explicitly name your indexes (don't rely on the auto-generated DB ones)

## Comparison vs other tools

* [alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html), as far as I can tell, requires you to generate a skeleton python file then fill it in yourself
* [sqlite sqldiff.exe](https://www.sqlite.org/sqldiff.html) can diff schemas but operates on full sqlite databases and I'm not sure if it outputs DDL
* liquibase might have a [diffing system](https://www.liquibase.org/documentation/diff.html) but from the docs it looks like it's outputting XML. And [they advise you not to use it](http://www.liquibase.org/2007/06/the-problem-with-database-diffs.html)
* [redgate sql compare](https://documentation.red-gate.com/sc/sql-server-management-studio-add-in/getting-started-with-the-add-in) seems to support comparing 'create table' schemas across git versions, although it looks like you have to find the SHAs by hand in a GUI

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
