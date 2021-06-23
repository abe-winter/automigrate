# automigrate

Automigrate is a command-line tool for ORM-less SQL migrations.
Unlike other migration tools, it uses git history to do diffs on `create table` statements instead of storing the migration history in a folder somewhere.

* [How is this different](#how-is-this-different)
* [Usage](#usage)
* [Advanced features](#advanced-features)

## How is this different

This tool uses git history to infer database migrations, and uses git SHAs to version production databases.

Other schema migration tools typically work by diffing ORM definitions against a live database (which can be your local DB).
Often these diffs are then checked into a folder in your project repo.

Seriously, all you have to do is maintain a file like this:

```sql
-- schema.sql
create table whatever (
  userid uuid primary key,
  age_at_birth int default 0
);
```

And when you add a field to the create table statement, automig figures out the 'alter table'.

## Usage

If you're using postgres:

```bash
pip install automig[postgres]
# set an environment var with postgres connection details
export AUTOMIG_CON=postgresql://postgres:$PGPASSWORD@host
# initialize the postgres DB to schema/*.sql -- do this once to create a DB
automig_pg --glob 'schema/*.sql' init
# update your DB to whatever sha is at git HEAD -- do this whenever your schema changes
automig_pg --glob 'schema/*.sql' update
# do a dry-run, show the output without applying it
automig_pg --preview --glob 'schema/*.sql' update
```

If you're using another database, you can get the raw SQL for these actions by using the `automig` tool instead of `automig_pg`. (docs coming soon).

Postgres is the primary database I test on, with sqlite support secondary.

## Advanced features

* [Instructions for doing kube-native migrations](./kube) are in the `kube` folder.
* Lambda support: you'll need to bundle a binary version of git that's compatible with amazonlinux. Post an issue if you need help with this.
* You can skip over bad diffs using `--opaque` mode, docs coming soon
* You can specify manual overrides for erroring diffs, or skip over whole shas, by using [.manualmig.yml file](./.manualmig.yml). docs coming soon but in the meantime look inside that file for an example.
* Convert an existing DB to use automig -- please post a github issue if you have this issue and I'll add instructions

### Generate ORM definitions from SQL

Experimental sqlalchemy generator in sa_harness.py. Try it out with:

```bash
python -m automig.lib.sa_harness 'test/schema/*.sql'
```
