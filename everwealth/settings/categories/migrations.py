from asyncpg import Connection


async def create_categories_table(conn: Connection):
    await conn.execute(
        """
            CREATE TABLE categories(
                id serial PRIMARY KEY,
                data JSONB
            )
        """
    )
    await conn.execute("CREATE INDEX categories_index ON categories USING GIN (data)")
