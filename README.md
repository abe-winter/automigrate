# automigrate

Tool to diff SQL schemas in git and apply the migrations.

## Beta software

This tool's output should be checked by an expert before applying it to a database.

## Installation & basic use

To install, `pip install git+https://github.com/abe-winter/automigrate`. This should install dependencies and register the automig command in your virtualenv.

Typical invocations:

```
# create an initial migration (also create meta tables)
automig HEAD 'schema/*.sql' --initial > migration.sql

# run directly with psql
automig HEAD 'schema/*.sql' | psql

# migrate a database
psql -c "select * from migrations where "
```

## Features

* operate on `*.sql` files (i.e. files with `create table`, `create index`, and possibly `insert` stmts) 
* operate on git -- meaning that it knows the git version of the last applied migration and can diff vs 
* **doesn't** inspect live SQL schemas (yet -- but we should at minimum do this to check that the target db is as expected)
* store history of applied migrations in sql in some kind of meta table

## What does & doesn't work

* Adding tables, indexes and columns should mostly work
* modifying primary keys doesn't work
* modifying column types doesn't work (even something inoccuous like a default)
* You can skip a diff, skip errors for a diff, or override a diff by ...
* be careful with using unescaped keywords as names (i.e. a table named table) -- you'll likely confuse the parser even if your sql engine allows it
* migrations meta tables are created by first run and upated by migrations, but you need to manually query them to know the last-applied migration (todo: what's the query?)
* this hasn't been tested on a wide range of syntax (i.e. arrays / json)
* What happens when metadata schema changes?

## Manually overriding migrations

In cases where the tool generates a migration you don't like, you can use a `.manual-automigrate.py` file in the working directory to override changes and suppress errors.

The format of this file is ...

The override key is `(sha, type, tablename, item_name)` and will be output with migration errors and in verbose mode.

Manual changes are logged in the meta tables so you can inspect the history in a pinch.

## Vs other tools

* alembic / other auto migration generators
	- they're generally language-specific and ORM-specific, this isn't
	- they're not git-aware so you need to manage migration files
	- they can usually connect to your DB -- this is designed to be run directly as SQL
* apex sql diff
	- they can operate on 'script folders' and integrate with source control
	- not sure what this means in practice
	- I think this product is GUI-first and only runs on windows?
* sqlite sqldiff.exe
	- seems like a really good tool if you're operating on `.sqlite` files
* liquibase
	- supports 4 formats for migration (xml, yml, json, sql) -- this supports 0 because it doesn't need them
	- requires you to explictly define migrations (I think) -- this doesn't

## Using with ORMs

Your ORM has to be willing to import a schema from create table statements. (I don't know any ORM that does this out of the box, although some can reflect a live DB).

This project (todo) comes with a harness that reads create table commands into a SQLAlchemy schema. Happy to accept PRs to do this with other languages / ORMs.

## Git edge cases

* Run with working directory (i.e. non-committed changes). (todo support this)
* What happens when a create table statement moves between files? Should work out of the box.
* What happens when a file is deleted? (todo support this)
