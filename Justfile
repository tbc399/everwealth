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

clear-db:
    @printf 'This will truncate all public tables except schema_migrations. Type "clear" to continue: '; read -r confirm; if [[ "$confirm" != "clear" ]]; then echo "Aborted."; exit 1; fi; python -c $'import asyncio, os\nimport asyncpg\n\nasync def main():\n    conn = await asyncpg.connect(os.environ["DATABASE_URL"])\n    try:\n        tables = await conn.fetch("""\n            SELECT format(\'%I.%I\', schemaname, tablename) AS name\n            FROM pg_tables\n            WHERE schemaname = \'public\'\n              AND tablename <> \'schema_migrations\'\n            ORDER BY tablename\n        """)\n        if not tables:\n            print("No tables to truncate.")\n            return\n        async with conn.transaction():\n            await conn.execute("TRUNCATE TABLE " + ", ".join(row["name"] for row in tables) + " RESTART IDENTITY CASCADE")\n        print(f"Truncated {len(tables)} tables.")\n    finally:\n        await conn.close()\n\nasyncio.run(main())'

plaid-fire-transactions-webhook access_token:
    curl --fail-with-body -sS -X POST https://sandbox.plaid.com/sandbox/item/fire_webhook \
        -H 'Content-Type: application/json' \
        -d '{"client_id":"{{ env_var("PLAID_CLIENT_ID") }}","secret":"{{ env_var("PLAID_SECRET") }}","access_token":"{{ access_token }}","webhook_type":"TRANSACTIONS","webhook_code":"SYNC_UPDATES_AVAILABLE"}'
