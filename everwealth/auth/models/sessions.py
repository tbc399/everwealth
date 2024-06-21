from datetime import datetime, timedelta
from operator import attrgetter
from typing import Optional

import shortuuid
from asyncpg import Connection
from cryptography.fernet import Fernet
from itsdangerous import Serializer
from loguru import logger
from pydantic import BaseModel, EmailStr, Field, IPvAnyAddress, PositiveInt


# TODO: how to make "long lived" sessions?
# DB stored sessions vs encrypted sessions stored in the cookies
# If they're stored on the server then there is more control to block, invalidate, exchange, etc...
# TODO: sessions need to be specific to the device the user is using
# TODO: expire and replace sessions on a regular basis (old sessions would have to be invalidated somehow)
# Maybe we could cache db sessions to make them fast!?
class Session(BaseModel):
    id: str = Field(default_factory=lambda: shortuuid.random(length=64))  # a short uuid
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=10))
    otp_id: str  # the otp this session was generated from
    user_id: str
    device_id: Optional[str] = Field(default="")  # TODO: is there a way to get this??
    device_trusted: Optional[bool] = Field(default=False)
    invalidated: Optional[bool] = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_expired(self):
        return self.expiry < datetime.utcnow()


async def create(user_id: str, otp_id: str, conn: Connection):
    session = Session(user_id=user_id, otp_id=otp_id)
    columns = ",".join(
        [
            "id",
            "expiry",
            "otp_id",
            "user_id",
            "device_id",
            "device_trusted",
            "invalidated",
            "created_at",
            "updated_at",
        ]
    )
    values = f"'{session.id}','{session.expiry}','{session.otp_id}','{session.user_id}', \
    '{session.device_id}',{session.device_trusted},{session.invalidated},'{session.created_at}',\
    '{session.updated_at}'"
    async with conn.transaction():
        await conn.execute(f"INSERT INTO sessions ({columns}) VALUES ({values})")
    return session


async def invalidate(id: str, conn: Connection):
    async with conn.transaction():
        # TODO: learn how to replace with proper prepared statements
        await conn.execute(f"UPDATE sessions SET invalidated = true WHERE id = '{id}'")


async def fetch(id: str, conn: Connection):
    sql = f"SELECT * FROM sessions WHERE id = '{id}'"
    logger.debug(f"executing sql: {sql}")
    row = await conn.fetchrow(sql)
    if row:
        return Session.model_validate(dict(row))
    return None


async def fetch_latest_active(user_id: str, conn: Connection):
    now = datetime.utcnow()
    sql = f"SELECT * FROM sessions WHERE user_id = '{user_id}' AND NOT invalidated"
    logger.debug(f"executing sql: {sql}")
    rows = await conn.fetch(sql)
    if rows:
        logger.debug(f"found {len(rows)}")
        sessions = sorted(
            (Session.model_validate(dict(x)) for x in rows), key=attrgetter("created_at")
        )
        active_sessions = [x for x in sessions if x.expiry > now]
    else:
        return None
    return active_sessions[-1] if active_sessions else None


async def fetch_by_otp_id(otp_id: str, conn: Connection):
    sql = f"SELECT * FROM sessions WHERE otp_id = '{otp_id}'"
    logger.debug(f"executing sql: {sql}")
    row = await conn.fetchrow(sql)
    if row:
        return Session.model_validate(dict(row))
    return None
