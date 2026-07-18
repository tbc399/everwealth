import asyncio
import sys
from pathlib import Path

import asyncpg
from everwealth.config import settings


async def run():
    sql_path = sys.argv[1]
    sql_file_path = Path.cwd() / sql_path

    if not sql_file_path.exists():
        print(f"{sql_path} does not exist")
        return -1

    print(f"Executing migration {sql_file_path}")

    connection = await asyncpg.connect(settings.database_url)

    contents = sql_file_path.read_text()
    await connection.execute(contents)

    await connection.close()


asyncio.run(run())
