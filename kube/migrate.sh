#!/usr/bin/env bash
# migrate.sh -- run migration against a postgres DB

set -euo pipefail

HEAD=$(git rev-parse HEAD)
TARGET=${TARGET:-$HEAD}

# runs automig with --init to setup the migration tables
# call this to set up automig on a fresh DB
init_automig() {
	# note: eval here is because AUTOMIG_GLOB has single-quotes and needs to be unquoted here
	eval "automig $TARGET $AUTOMIG_GLOB --initial" | psql $AUTOMIG_CON --single-transaction
}

# helper for preview / update. sets LAST_SHA, RANGE
range() {
	local LAST_SHA=$(psql $AUTOMIG_CON -t -c "select sha from automigrate_meta order by id desc limit 1")
	RANGE=$LAST_SHA...$TARGET
	echo "RANGE is $RANGE"
}

# previews the automigrate command without changing the DB
preview_automig() {
	range
	eval "automig $RANGE $AUTOMIG_GLOB"
}

# applies a migration
update_automig() {
	range
	eval "automig $RANGE $AUTOMIG_GLOB"
	eval "automig $RANGE $AUTOMIG_GLOB" | psql $AUTOMIG_CON --single-transaction
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
