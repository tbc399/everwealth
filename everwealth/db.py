from asyncpg import Pool

#  until we can find a better way to do this
pool: Pool = None


async def get_connection():
    if not pool:
        raise ValueError("asyncpg connection pool is not initialized")
    async with pool.acquire() as connection:
        yield connection
