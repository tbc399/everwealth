import asyncio
import sys
from pathlib import Path

import asyncpg
from config import settings


async def run():
    sql_path = sys.argv[1]
    sql_file_path = Path.cwd() / sql_path

    if not sql_file_path.exists():
        print(f"{sql_path} does not exist")
        return -1

    print(f"Executing migration {sql_file_path}")

    connection = await asyncpg.connect(settings.database_url)

    with open(sql_file_path, "r") as f:
        contents = f.read()
        statements = contents.split(";")
        for statement in statements:
            if len(statement.strip()) and not statement.startswith("--"):
                print(f"Executing statement {statement}")
                try:
                    await connection.execute(statement)
                except asyncpg.exceptions.DuplicateObjectError:
                    print("Object already exists")

    await connection.close()


asyncio.run(run())
