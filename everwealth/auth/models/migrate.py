from asyncpg import Connection


async def create_sessions_table(conn: Connection):
    await conn.execute(
        """
            CREATE TABLE sessions(
                id serial PRIMARY KEY,
                data JSONB
            )
        """
    )
    await conn.execute("CREATE INDEX sessions_index ON sessions USING GIN (data)")


async def create_otp_table(conn: Connection):
    await conn.execute(
        """
            CREATE TABLE otp(
                id serial PRIMARY KEY,
                data JSONB
            )
        """
    )
    await conn.execute("CREATE INDEX otp_index ON otp USING GIN (data)")
