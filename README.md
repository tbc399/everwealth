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
