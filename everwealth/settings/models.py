from pydantic import BaseModel
from typing import Optional
from asyncpg import Connection
from datetime import datetime
from everwealth.users import User
from shortuuid import uuid
from pydantic import Field


class Category(BaseModel):
    id: str = Field(default_factory=uuid)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = None


async def create(name: str, user: User, conn: Connection):
    categories = await fetch_many(conn)
    #if name not in categories:
    #    category = Category(name=name, user=user)
    await conn.execute(f"INSERT INTO categories () VALUES ('{user.model_dump_json()}')")
    return category


async def fetch(name: str, conn: Connection):
    record = await conn.fetch(f'SELECT data from users where data @> \'{{"name": "{name}"}}\'')
    return Category(record[0])


async def fetch_many(conn: Connection):
    records = await conn.fetch(f'SELECT data from users where data @> \'{{"email": "{email}"}}\'')
    return


# TODO: should categories have a hierarchy, e.g. "Entertainment" with sub
# categories of "Movies", "Date Night", etc...
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
    "Vehicle Maintenance"
]
