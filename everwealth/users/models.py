from typing import Optional
from starlette.authentication import BaseUser

from shortuuid import uuid
from asyncpg import Connection
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel, BaseUser):
    id: str = Field(default_factory=uuid)  # short uuid
    first: Optional[str] = None
    last: Optional[str] = None
    email: EmailStr  # TODO: is this necessary?


async def fetch(email: str, conn: Connection):
    row = await conn.fetchrow(f'SELECT data from users where data @> \'{{"email": "{email}"}}\'')
    if row:
        return User.model_validate_json(row["data"])
    return None


async def create(email: str, conn: Connection, first: str = None, last: str = None):
    user = User(email=email)
    await conn.execute(f"INSERT INTO users (data) VALUES ('{user.model_dump_json()}')")
    return user
