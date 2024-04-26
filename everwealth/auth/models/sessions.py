from pydantic import Field, IPvAnyAddress, BaseModel, PositiveInt, EmailStr
from operator import attrgetter
from datetime import datetime, timedelta
import shortuuid
from typing import Optional
from asyncpg import Connection


# TODO: how to make "long lived" sessions?
class Session(BaseModel):
    id: str = Field(default_factory=lambda: shortuuid.random(length=64))  # a short uuid
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=1))
    user_id: str
    device_id: Optional[str] = Field(default="")  # TODO: is there a way to get this??
    device_trusted: Optional[bool] = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invalidated: Optional[bool] = Field(default=False)


async def create(user: str):
    return


async def invalidate(id: str, conn: Connection):
    async with conn.transaction():
        # TODO: learn how to replace with proper prepared statements
        await conn.execute(
            f"UPDATE sessions SET data['invalidated'] = true where data['id'] = '\"{id}\"'"
        )


async def fetch(id: str):
    return


async def fetch_latest_active(user_id: str, conn: Connection):
    now = datetime.utcnow()
    rows = await conn.fetch(
        f"SELECT data FROM sessions WHERE data['user_id'] = '\"{user_id}\"' AND data['invalidated'] = 'false'"
    )
    if rows:
        sessions = sorted((Session.model_validate_json(x["data"]) for x in rows), key=attrgetter('created_at'))
        active_sessions = [x for x in sessions if x.expiry < now]
    else:
        return None
    return active_sessions[-1] if active_sessions else None
