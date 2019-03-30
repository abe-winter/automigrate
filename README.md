# automigrate

Tool to diff SQL schemas in git and apply the migrations.

## Beta software

This tool's output should be checked by an expert before applying it to a database.

## Installation & basic use

To install, `pip install git+https://github.com/abe-winter/automigrate`. This should install dependencies and register the automig command in your virtualenv.

Typical invocations:

```
# create an initial migration (also create meta tables)
automig 218dd2c 'test/schema/*.sql' --initial | psql -h 172.17.0.2 -U postgres --single-transaction

# migrate a database
LAST_SHA=$(psql -h 172.17.0.2 -U postgres -t -c "select sha from automigrate_meta order by id desc limit 1")
echo migrating from $LAST_SHA
automig $LAST_SHA...b5b40ce 'test/schema/*.sql' | psql -h 172.17.0.2 -U postgres --single-transaction

# I guess you can just migrate to HEAD if you're feeling lucky
automig $LAST_SHA...HEAD 'test/schema/*.sql' | psql -h 172.17.0.2 -U postgres --single-transaction
```

## Features

* operate on `*.sql` files (i.e. files with `create table` and `create index` statements)
* operate on git -- meaning that it tracks the git version of applied migration and can create a SQL migration given two git refs
* store history of applied migrations in sql in `automigrate_meta` table
* **doesn't** inspect live SQL schemas (yet -- but we should at minimum do this to check that the target db is as expected)

## What does & doesn't work

* Adding tables, indexes and columns should mostly work
* modifying primary keys doesn't work
* modifying column types doesn't work (even something inoccuous like a default)
* For diffs that are erroring, you can override with a [.manualmig.yml file](./.manualmig.yml)
* Be careful with using unescaped keywords as names (i.e. a table named table) -- you'll likely confuse the parser even where your sql engine allows it
* This hasn't been tested on a wide range of syntax (i.e. arrays / json)
* Not sure if capitalized SQL keywords are supported (todo add tests)
* Arbitrary whitespace changes -- probably not (todo add tests)

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
