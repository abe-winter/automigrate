#!/usr/bin/env bash
# migrate.sh -- run migrations against a postgres db

set -euo pipefail

HEAD=$(git rev-parse HEAD)

# runs automig with --init to setup the migration tables
# call this to set up automig on a fresh DB
init_automig() {
	automig $HEAD $AUTOMIG_GLOB --initial | psql -h $AUTOMIG_HOST -U postgres --single-transaction
}

# helper for preview / update. sets AUTOMIG_HOST, RANGE
range() {
	local LAST_SHA=$(psql -h $AUTOMIG_HOST -U postgres -t -c "select sha from automigrate_meta order by id desc limit 1")
	RANGE=$LAST_SHA...$HEAD
	echo "RANGE is $RANGE"
}

# previews the automigrate command without changing the DB
preview_automig() {
	range
	automig $RANGE $AUTOMIG_GLOB
}

# applies a migration
update_automig() {
	range
	automig $RANGE $AUTOMIG_GLOB
	automig $RANGE $AUTOMIG_GLOB | psql -h $AUTOMIG_HOST -U postgres --single-transaction
}

usage() {
	echo "pass --init, --preview or --update pls"
	exit 1
}

case $1 in
	--init ) init_automig;;
	--preview ) preview_automig;;
	--update ) update_automig;;
	--help ) usage;;
esac
