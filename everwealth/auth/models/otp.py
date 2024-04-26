from pydantic import Field, EmailStr, PositiveInt, BaseModel
import shortuuid
from typing import Optional
from datetime import datetime, timedelta
import random
from asyncpg import Connection
from loguru import logger


class OneTimePass(BaseModel):
    id: str = Field(default_factory=shortuuid.uuid)
    magic_token: str = Field(default_factory=lambda: shortuuid.random(length=64))
    code: PositiveInt = Field(default_factory=lambda: random.randint(1000,9999))
    email: EmailStr
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invalidated: Optional[bool] = Field(default=False)
    

async def create(email: str, conn: Connection):
    otp = OneTimePass(email=email)
    await conn.execute(f"INSERT INTO otp (data) VALUES ('{otp.model_dump_json()}')")
    return otp


async def fetch(id: str, conn: Connection):
    row = await conn.fetchrow(f'SELECT data from otp where data @> \'{{"id": "{id}"}}\'')
    if row:
        return OneTimePass.model_validate_json(row["data"])
    return None


async def fetch_by_magic_token(magic_token: str, conn: Connection):
    row = await conn.fetchrow(f'SELECT data from otp where data @> \'{{"magic_token": "{magic_token}"}}\'')
    if row:
        return OneTimePass.model_validate_json(row["data"])
    return None


async def invalidate(id: str, conn: Connection):
    async with conn.transaction():
        # TODO: learn how to replace with proper prepared statements
        await conn.execute(
            f"UPDATE otp SET data['invalidated'] = true where data['id'] = '\"{id}\"'"
        )


async def send_email(email: str, otpass: OneTimePass):
    magic_url = f"/login/validate?token={otpass.magic_token}"
    logger.info(f"magic url: {magic_url}")
    logger.info(f"sending otp email to {email}")


