from datetime import datetime
from typing import Optional

from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, Field
from shortuuid import uuid


class Category(BaseModel):
    id: str = Field(default_factory=uuid)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


async def create(name: str, user_id: str, db: Connection):
    categories = await fetch_many(user_id, db)
    if name not in categories:
        category = Category(name=name, user_id=user_id)
    category = Category(name=name, user_id=user_id)
    await db.execute(f"INSERT INTO categories (data) VALUES ('{category.model_dump_json()}')")
    return category


async def fetch(id: str, user_id: str, db: Connection):
    sql = f'SELECT data from categories where data @> \'{{"id": "{id}", "user_id": "{user_id}"}}\''
    logger.debug(f"Executing SQL: {sql}")
    record = await db.fetchrow(sql)
    return Category.model_validate_json(record["data"])


async def fetch_many(user_id: str, db: Connection):
    logger.debug(f"Fetching categories for {user_id}")
    # TODO: filter on user id
    records = await db.fetch(
        f'SELECT data from categories where data @> \'{{"user_id": "{user_id}"}}\''
    )
    return [Category.model_validate_json(x["data"]) for x in records]


# TODO: should categories have a hierarchy, e.g. "Entertainment" with sub
# categories of "Movies", "Date Night", etc...
# TODO: add these back in. Will have to determine how we associsat these with each user
default_category_names = [
    "Groceries",
    "Gas",
    "Entertainment",
    "Electricity",
    "Mortgage",
    "Rent",
    "Restaurant",
    "Electricity",
    "Internet",
    "Utilities",
    "Vehicle Maintenance",
]
