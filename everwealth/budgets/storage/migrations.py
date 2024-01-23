from asyncpg import Connection


async def create_budgets_table(conn: Connection):
    await conn.execute(
        '''
            CREATE TABLE budgets(
                id serial PRIMARY KEY,
                data JSONB
            )
        '''
    )
    await conn.execute(
        "CREATE INDEX budget_index ON budgets USING GIN (data)"
    )
