#!/bin/sh
set -eu

# Keep the URL's SSL options intact; use an explicit override if necessary.
export DATABASE_URL="${DBMATE_DATABASE_URL:-${DATABASE_URL:?DATABASE_URL is required}}"
exec dbmate --migrations-dir db/migrations --no-dump-schema --wait migrate
