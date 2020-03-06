# automigrate

Tool to diff SQL schemas in git and apply the migrations.

* [How is this different](#how-is-this-different)
* [Usage](#usage)
* [Advanced features](#advanced-features)

## How is this different

Other schema migration tools work in one of two ways:

* Check in 'up' and 'down' migrations, which then get applied to your DB ([alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html) et al). These are most often manual.
* Compare a live DB to a source of truth and apply the changes ([sqldiff.exe](https://www.sqlite.org/sqldiff.html), [migra](https://github.com/djrobstep/migra), [pgquarrel](https://github.com/eulerto/pgquarrel))

This tool only requires you to create and edit the desired state of your database, i.e. a file or folder full of `create table` and `create index` statements. This tool looks at the git history of that file and automatically infers the DDL statements to get from and old point in history to the new one.

The **one big difference** is that you don't have to write migrations ever! And every running database has a git version, so you can up- and downgrade it to a desired git sha.

## Usage

If you're using postgres:

```bash
pip install automig[postgres]
# set an environment var with postgres connection details
export AUTOMIG_CON=postgresql://postgres:$PGPASSWORD@host
# initialize the postgres DB to schema/*.sql
automig_pg --glob 'schema/*.sql' init
# update your DB to whatever sha is at git HEAD
automig_pg --glob 'schema/*.sql' update
# do a dry-run, show the output without applying it
automig_pg --preview --glob 'schema/*.sql' update
```

If you're using another database, you can get the raw SQL for these actions by using the `automig` tool instead of `automig_pg`. (docs coming soon).

## Advanced features

* [Instructions for doing kube-native migrations](./kube) are in the `kube` folder.
* You can skip over bad diffs using `--opaque` mode, docs coming soon
* You can specify manual overrides for erroring diffs by using [.manualmig.yml file](./.manualmig.yml), docs coming soon.

### Generate ORM definitions from SQL

Experimental sqlalchemy generator in sa_harness.py. Try it out with:

```bash
python -m automig.lib.sa_harness 'test/schema/*.sql'
```
