from pydantic import Field, IPvAnyAddress, BaseModel, PositiveInt, EmailStr
from operator import attrgetter
from datetime import datetime, timedelta
import shortuuid
from typing import Optional
from asyncpg import Connection
from loguru import logger
from itsdangerous import Serializer
from cryptography.fernet import Fernet


# TODO: how to make "long lived" sessions?
# DB stored sessions vs encrypted sessions stored in the cookies
# If they're stored on the server then there is more control to block, invalidate, exchange, etc...
# TODO: sessions need to be specific to the device the user is using
# TODO: expire and replace sessions on a regular basis (old sessions would have to be invalidated somehow)
# Maybe we could cache db sessions to make them fast!?
class Session(BaseModel):
    id: str = Field(default_factory=lambda: shortuuid.random(length=64))  # a short uuid
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=1))
    otp_id: str  # the otp this session was generated from
    user_id: str
    device_id: Optional[str] = Field(default="")  # TODO: is there a way to get this??
    device_trusted: Optional[bool] = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invalidated: Optional[bool] = Field(default=False)

    def is_expired(self):
        return self.expiry < datetime.utcnow()


async def create(user_id: str, otp_id: str, conn: Connection):
    session = Session(user_id=user_id, otp_id=otp_id)
    async with conn.transaction():
        await conn.execute(f"INSERT INTO sessions (data) VALUES ('{session.model_dump_json()}')")


async def invalidate(id: str, conn: Connection):
    async with conn.transaction():
        # TODO: learn how to replace with proper prepared statements
        await conn.execute(
            f"UPDATE sessions SET data['invalidated'] = true where data['id'] = '\"{id}\"'"
        )


async def fetch(id: str, conn: Connection):
    sql = f"SELECT data FROM sessions WHERE data['id'] = '\"{id}\"'"
    logger.debug(f"executing sql: {sql}")
    row = await conn.fetchrow(sql)
    if row:
        return Session.model_validate_json(row["data"])
    return None


async def fetch_latest_active(user_id: str, conn: Connection):
    now = datetime.utcnow()
    sql = f"SELECT data FROM sessions WHERE data['user_id'] = '\"{user_id}\"' AND data['invalidated'] = 'false'"
    logger.debug(f"executing sql: {sql}")
    rows = await conn.fetch(sql)
    if rows:
        logger.debug(f"found {len(rows)}")
        sessions = sorted(
            (Session.model_validate_json(x["data"]) for x in rows), key=attrgetter("created_at")
        )
        active_sessions = [x for x in sessions if x.expiry > now]
    else:
        return None
    return active_sessions[-1] if active_sessions else None


async def fetch_by_otp_id(otp_id: str, conn: Connection):
    sql = f"SELECT data FROM sessions WHERE data['otp_id'] = '\"{otp_id}\"'"
    logger.debug(f"executing sql: {sql}")
    row = await conn.fetchrow(sql)
    if row:
        return Session.model_validate_json(row["data"])
    return None
