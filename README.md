## Railway deployment

The root `Dockerfile` builds the DaisyUI CSS and JavaScript, installs Python
dependencies, and runs Uvicorn as a non-root user on Railway's `PORT`. Node and
`node_modules` are not included in the runtime image. Lucette is bundled under
`vendor/lucette` so deployment does not depend on a sibling checkout.

1. Push this repository to GitHub, then create a Railway project with a PostgreSQL
   service and an application service connected to this repository. Keep the
   application root directory at the repository root and use the Dockerfile builder.
2. Set the application service variables below. Replace `Postgres` in the reference
   variables if your database service has a different name.
3. In the application service's deployment settings, set **Pre-deploy Command** to
   `sh scripts/migrate.sh`, **Healthcheck Path** to `/health`, and the healthcheck
   timeout to 60 seconds. Leave the start command unset to use the Dockerfile CMD.
   Use restart-on-failure and one replica.
4. Generate a public domain in Railway's networking settings, set
   `PLAID_WEBHOOK_HANDLER_URL` to
   `https://YOUR-DOMAIN/transactions/hooks/plaid`, and deploy.
5. Check that `/health` returns `{"status":"ok"}`, open `/register`, and connect
   a sandbox account before switching to production Plaid credentials.

Required application variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway private connection) |
| `DBMATE_DATABASE_URL` | `${{Postgres.DATABASE_URL}}?sslmode=disable` for Railway's private PostgreSQL connection |
| `AUTH_TOKEN_SECRET` | A unique, long random secret; generate with `openssl rand -hex 32` |
| `SESSION_COOKIE_SECURE` | `true` (Railway serves public traffic over HTTPS) |
| `FORWARDED_ALLOW_IPS` | `*` behind Railway's trusted ingress, so generated asset URLs use HTTPS |
| `PLAID_CLIENT_ID` | Your Plaid client ID |
| `PLAID_SECRET` | Your Plaid secret for the selected environment |
| `PLAID_ENV` | `sandbox` initially; `production` when ready |
| `PLAID_WEBHOOK_HANDLER_URL` | Your public HTTPS URL ending in `/transactions/hooks/plaid` |

Never commit real credentials or upload `.env` to your image. `.env.example`
lists local settings; Railway injects variables at runtime. Keep
`AUTH_TOKEN_SECRET` stable across redeploys so existing sessions remain valid.
Only trust all forwarded headers when the application is reachable exclusively
through a trusted reverse proxy; do not use `FORWARDED_ALLOW_IPS=*` on an exposed
Uvicorn server. Locally, leave it unset (Uvicorn trusts loopback by default).
For an external TLS-enabled database, set `DBMATE_DATABASE_URL` to its appropriate
TLS connection URL instead. If a URL already has query parameters, append further
parameters with `&`, not a second `?`.

The migration command applies pending SQL migrations to the existing database
and fails the deployment on error. It does not create or reset databases, and it
does not require `pg_dump`. Back up existing data before first deploying; an
existing database must have its dbmate migration history in sync with its schema.
Railway's [pre-deploy command documentation](https://docs.railway.com/deployments/pre-deploy-command)
describes how this step gates application startup.

Use **one replica and one worker**, and leave serverless sleeping disabled: the
budget rollover scheduler and Lucette's in-memory event queue run in the web
process. Move those jobs to coordinated workers before scaling horizontally.
No application volume is required; durable data lives in PostgreSQL. Configure
database backups in Railway separately. SMTP variables from the sign-in email
section below are needed only if you use OTP email sign-in.

To test the same image locally against a disposable database:

```sh
docker build -t everwealth .
docker run --rm --env-file .env everwealth sh scripts/migrate.sh
docker run --rm --env-file .env -e PORT=8000 -p 8000:8000 everwealth
```

The database URL must be reachable from inside Docker, not `localhost` unless
PostgreSQL is in the same container. On Docker Desktop, use
`host.docker.internal` for a database running on the host. For local HTTP, keep
`SESSION_COOKIE_SECURE=false`. Local Poetry users should run `poetry lock` and
`poetry install` after this change to pick up the bundled Lucette path.

## UI assets

The interface uses DaisyUI with the `light` and `dark` themes. Build the
production CSS and the bundled Lucide icons after changing templates or UI scripts:

```sh
npm install
npm run build
```

Use `npm run dev:css` to watch template and stylesheet changes locally.

Tailwind CSS 4 and DaisyUI 5 use CSS-based configuration. To change palettes,
update `themes` in the `@plugin "daisyui"` block in `everwealth/static/input.css`
and the theme attributes on `<html>` in `everwealth/templates/base.html`.
The startup script and toggle read those attributes. Rebuild the assets and
refresh the browser after changing themes.

## Database migrations

This project uses [dbmate](https://github.com/amacneil/dbmate) with plain SQL
migrations in `db/migrations`.

Install dbmate:

```sh
go install github.com/amacneil/dbmate/v2@latest
```

Run pending migrations:

```sh
just migrate
```

Check migration status:

```sh
just migrate-status
```

Create a new migration:

```sh
just migration add_some_change
```

The Just recipes default to `$HOME/go/bin/dbmate`. Set `DBMATE=/path/to/dbmate`
to use a different binary, and set `DBMATE_DATABASE_URL` to override the
database URL used by dbmate.

## Sign-in email

The OTP sign-in flow sends email through SMTP. Configure these environment
variables:

```sh
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=no-reply@example.com
SMTP_USE_TLS=true
```

If your SMTP server does not require authentication, leave `SMTP_USERNAME` and
`SMTP_PASSWORD` unset.
