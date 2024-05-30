from typing import Annotated, Optional

from asyncpg import Connection
from fastapi import Cookie, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, EmailStr, Field
from shortuuid import uuid
from starlette.authentication import BaseUser

from everwealth.auth import sessions
from everwealth.db import get_connection


class User(BaseModel, BaseUser):
    id: str = Field(default_factory=uuid)  # short uuid
    first: Optional[str] = None
    last: Optional[str] = None
    email: EmailStr  # TODO: is this necessary?


async def fetch(id: str, conn: Connection):
    row = await conn.fetchrow(f'SELECT data from users where data @> \'{{"id": "{id}"}}\'')
    if row:
        return User.model_validate_json(row["data"])
    return None


async def create(email: str, conn: Connection, first: str = None, last: str = None):
    user = User(email=email)
    await conn.execute(f"INSERT INTO users (data) VALUES ('{user.model_dump_json()}')")
    return user


# maybe split this out to its own file?
async def auth_user(
    session: Annotated[str | None, Cookie()], db: Connection = Depends(get_connection)
):
    if session is None:
        logger.info("No session found")
        raise HTTPException()

    # TODO: cache sessions here to save time
    session: sessions.Session = await sessions.fetch(session, db)
    if session and session.is_expired():
        logger.info(f"Session {session} is no longer valid")
        raise HTTPException(status_code=401)

    return session.user_id
