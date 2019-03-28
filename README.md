# automigrate

Tool to diff SQL schemas in git and apply the migrations.

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

## Beta software

This tool's output should be checked by an expert before applying it to a database.
