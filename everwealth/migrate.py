import asyncio

import asyncpg

from budgets.storage.migrations import create_budgets_table
from config import settings


async def run():
    connection = await asyncpg.connect(settings.database_url)

    await create_budgets_table(connection)

    await connection.close()


asyncio.run(run())
