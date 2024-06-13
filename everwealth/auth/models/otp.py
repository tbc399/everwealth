import random
from datetime import datetime, timedelta
from typing import Optional

import shortuuid
from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, EmailStr, Field, PositiveInt


class OneTimePass(BaseModel):
    id: str = Field(default_factory=shortuuid.uuid)
    magic_token: str = Field(default_factory=lambda: shortuuid.random(length=64))
    code: PositiveInt = Field(default_factory=lambda: random.randint(1000, 9999))
    email: EmailStr
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invalidated: Optional[bool] = Field(default=False)

    def is_expired(self):
        if self.invalidated:
            return True
        return self.expiry < datetime.utcnow()


async def create(email: str, conn: Connection):
    otp = OneTimePass(email=email)
    dump = otp.model_dump()
    columns = ",".join(
        ["id", "magic_token", "code", "email", "expiry", "created_at", "invalidated"]
    )
    values = f"'{otp.id}','{otp.magic_token}',{otp.code},'{otp.email}','{otp.expiry}','{otp.created_at}',{otp.invalidated}"
    print(values)
    async with conn.transaction():
        await conn.execute(f"INSERT INTO otp ({columns}) VALUES ({values})")
    return otp


async def fetch(id: str, conn: Connection):
    row = await conn.fetchrow(f"SELECT * FROM otp WHERE id = '{id}'")
    if row:
        return OneTimePass.model_validate(dict(row))
    return None


async def fetch_by_magic_token(magic_token: str, conn: Connection):
    row = await conn.fetchrow(f"SELECT * FROM otp WHERE magic_token = '{magic_token}'")
    if row:
        return OneTimePass.model_validate(dict(row))
    return None


async def invalidate(id: str, conn: Connection):
    async with conn.transaction():
        # TODO: learn how to replace with proper prepared statements
        await conn.execute(f"UPDATE otp SET invalidated = true WHERE id = '{id}'")


# TODO: move this guy out to a more "service-like" module
async def send_email(email: str, otpass: OneTimePass):
    # TODO: how to get the base url?
    magic_url = f"http://localhost:8000/login/validate/{otpass.magic_token}"
    logger.info(f"magic url: {magic_url}")
    logger.info(f"sending otp email to {email}")
