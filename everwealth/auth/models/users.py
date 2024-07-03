from datetime import datetime
from typing import Annotated, Optional

from asyncpg import Connection
from fastapi import Cookie, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, EmailStr, Field
from shortuuid import uuid
from starlette.authentication import BaseUser

from everwealth.db import get_connection

from . import sessions


class User(BaseModel, BaseUser):
    id: str = Field(default_factory=uuid)  # short uuid
    first: Optional[str] = None
    last: Optional[str] = None
    email: EmailStr  # TODO: is this necessary?
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


async def fetch(id: str, conn: Connection):
    row = await conn.fetchrow(f"SELECT * FROM users WHERE id = '{id}'")
    if row:
        return User.model_validate(dict(row))
    return None


async def fetch_by_email(email: str, db: Connection):
    row = await db.fetchrow(f"SELECT * FROM users WHERE email = '{email}'")
    if row:
        return User.model_validate(dict(row))
    return None


async def create(email: str, conn: Connection, first: str = None, last: str = None):
    user = User(email=email)
    dump = user.model_dump()
    columns = ",".join(dump.keys())
    values = dump.values()
    place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
    sql = f"INSERT INTO users ({columns}) VALUES ({place_holders})"
    logger.debug(f"Running sql {sql}")
    async with conn.transaction():
        await conn.execute(sql, *values)
    return user


# maybe split this out to its own file?
async def auth_user(
    request: Request,
    browser_session: Annotated[str | None, Cookie(alias="session")],
    db: Connection = Depends(get_connection),
):
    if browser_session is None:
        logger.info("No session found")
        raise HTTPException(status_code=401)

    # TODO: cache sessions here to save time
    session: sessions.Session = await sessions.fetch(browser_session, db)

    if session is None:
        raise HTTPException(status_code=401)

    if session.is_expired():
        logger.info(f"Session {session.id} is no longer valid")
        raise HTTPException(status_code=401)

    logger.debug(f"Session {session.id} is good")

    return session.user_id
