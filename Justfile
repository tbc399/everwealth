set dotenv-load

set shell := ["zsh", "-c"]

run:
    granian --interface asgi --loop uvloop --reload everwealth/main:app

migrate-go-features:
    python -m everwealth.migrate everwealth/migrations/port_go_features.sql

plaid-fire-transactions-webhook access_token:
    curl --fail-with-body -sS -X POST https://sandbox.plaid.com/sandbox/item/fire_webhook \
        -H 'Content-Type: application/json' \
        -d '{"client_id":"{{ env_var("PLAID_CLIENT_ID") }}","secret":"{{ env_var("PLAID_SECRET") }}","access_token":"{{ access_token }}","webhook_type":"TRANSACTIONS","webhook_code":"SYNC_UPDATES_AVAILABLE"}'
