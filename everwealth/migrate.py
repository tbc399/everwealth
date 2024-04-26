import asyncio

import asyncpg

# from budgets.storage.migrations import create_budgets_table
# from users.migration import create_users_table
# from settings.migrations import create_categories_table
# from transactions.migrations import create_transactions_table
from auth.models.migrate import create_otp_table, create_sessions_table
from config import settings


async def run():
    connection = await asyncpg.connect(settings.database_url)

    # await create_budgets_table(connection)
    # await create_users_table(connection)
    # await create_categories_table(connection)
    # await create_transactions_table(connection)
    await create_sessions_table(connection)
    await create_otp_table(connection)

    await connection.close()


asyncio.run(run())
