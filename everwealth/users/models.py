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


async def fetch_user(email: str, conn: Connection):
    # TODO: email needs to be validated. Can it be done as pydantic Form validation?
    row = await conn.fetchrow(f'SELECT data from users where data @> \'{{"email": "{email}"}}\'')
    print(row)
    return row


async def create_user(email: str, conn: Connection, first: str = None, last: str = None):
    user = User(email=email)
    await conn.execute(f"INSERT INTO users (data) VALUES ('{user.model_dump_json()}')")
    return user
