#!/usr/bin/env bash
# integration-test.sh -- integration test for automig_pg wrapper

set -euo pipefail
set -x

GLOB=test/schema/sql.sql

docker rm -fv $NAME
make backend
# reload for $DB_HOST
direnv reload
timeout 5 sh -c "until nc -z $DB_HOST 5432; do sleep 0.5; done"
automig_pg --glob $GLOB init
automig_pg --glob $GLOB update
