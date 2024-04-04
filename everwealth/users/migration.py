from asyncpg import Connection


async def create_users_table(conn: Connection):
    await conn.execute(
        """
            CREATE TABLE users(
                id serial PRIMARY KEY,
                data JSONB
            )
        """
    )
    await conn.execute("CREATE INDEX user_index ON users USING GIN (data)")
