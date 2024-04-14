from asyncpg import Connection


async def create_transactions_table(conn: Connection):
    await conn.execute(
        """
            CREATE TABLE transactions(
                id serial PRIMARY KEY,
                data JSONB
            )
        """
    )
    await conn.execute("CREATE INDEX transactions_index ON transactions USING GIN (data)")
