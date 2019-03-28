# automigrate

Tool to diff SQL schemas in git and apply the migrations.

## Features

* operate on `*.sql` files (i.e. files with `create table`, `create index`, and possibly `insert` stmts) 
* operate on git -- meaning that it knows the git version of the last applied migration and can diff vs 
* **doesn't** inspect live SQL schemas (yet -- but we should at minimum do this to check that the target db is as expected)
* store history of applied migrations in sql in some kind of meta table
