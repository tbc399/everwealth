set dotenv-load

set shell := ["zsh", "-c"]

dbmate_cmd := env_var_or_default("DBMATE", "$HOME/go/bin/dbmate")
dbmate_url := env_var_or_default("DBMATE_DATABASE_URL", env_var("DATABASE_URL") + "?sslmode=disable")

run:
    granian --interface asgi --loop uvloop --reload everwealth/main:app

format:
    black .
    isort .

dbmate *args:
    @{{ dbmate_cmd }} --url "{{ dbmate_url }}" --migrations-dir db/migrations {{ args }}

migrate:
    @{{ dbmate_cmd }} --url "{{ dbmate_url }}" --migrations-dir db/migrations up

migrate-status:
    @{{ dbmate_cmd }} --url "{{ dbmate_url }}" --migrations-dir db/migrations status

migration name:
    @{{ dbmate_cmd }} --url "{{ dbmate_url }}" --migrations-dir db/migrations new "{{ name }}"

plaid-fire-transactions-webhook access_token:
    curl --fail-with-body -sS -X POST https://sandbox.plaid.com/sandbox/item/fire_webhook \
        -H 'Content-Type: application/json' \
        -d '{"client_id":"{{ env_var("PLAID_CLIENT_ID") }}","secret":"{{ env_var("PLAID_SECRET") }}","access_token":"{{ access_token }}","webhook_type":"TRANSACTIONS","webhook_code":"SYNC_UPDATES_AVAILABLE"}'
