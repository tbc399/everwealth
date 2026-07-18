set dotenv-load

set shell := ["zsh", "-c"]

run:
    granian --interface asgi --loop uvloop everwealth/main:app

migrate-go-features:
    python -m everwealth.migrate everwealth/migrations/port_go_features.sql
