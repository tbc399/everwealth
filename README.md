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
