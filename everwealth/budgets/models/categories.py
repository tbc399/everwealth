from datetime import datetime
from typing import Optional, List

from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, Field, ConfigDict
from shortuuid import uuid
from enum import Enum


class CategoryType(Enum):
    income = "income"
    expense = "expense"


# TODO: Should we have a category/sub category design?
class Category(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=uuid)
    name: str
    type: CategoryType = Field(default=CategoryType.expense)
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


async def create(name: str, user_id: str, db: Connection):
    categories = await fetch_many(user_id, db)
    if name not in categories:
        category = Category(name=name, user_id=user_id)
    dump = category.model_dump()
    columns = ",".join(dump.keys())
    values = dump.values()
    place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
    category = Category(name=name, user_id=user_id)
    await db.execute(f"INSERT INTO categories ({columns}) VALUES ({place_holders})", *values)
    return category


async def create_many(categories: List[Category], user_id: str, db: Connection):
    async with db.transaction():
        await db.executemany(
            "INSERT INTO categories (id, name, user_id, created_at) VALUES ($1, $2, $3, $4)",
            ((x.model_dump().values(),) for x in categories),
        )


async def fetch(id: str, user_id: str, db: Connection):
    sql = f"SELECT * FROM categories WHERE id = '{id}' AND user_id = '{user_id}'"
    logger.debug(f"Executing SQL: {sql}")
    record = await db.fetchrow(sql)
    return Category.model_validate(dict(record))


async def fetch_many(user_id: str, db: Connection):
    logger.debug(f"Fetching categories for {user_id}")
    # TODO: filter on user id
    records = await db.fetch(f"SELECT * FROM categories WHERE user_id = '{user_id}'")
    return [Category.model_validate(dict(x)) for x in records]

