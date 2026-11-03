#!/bin/sh
set -eu

exec granian --interface asgi --loop uvloop --host 0.0.0.0 \
    --port "${PORT:-8000}" --workers 1 --no-reload --factory everwealth.asgi:create_app
