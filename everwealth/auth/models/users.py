from datetime import datetime
from typing import Annotated, Optional

from asyncpg import Connection
from fastapi import Cookie, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, EmailStr, Field
from shortuuid import uuid
from starlette.authentication import BaseUser

from everwealth.auth.tokens import AuthTokenError, decode_auth_token


class User(BaseModel, BaseUser):
    id: str = Field(default_factory=uuid)  # short uuid
    first: Optional[str] = None
    last: Optional[str] = None
    username: Optional[str] = None
    email: EmailStr  # TODO: is this necessary?
    password_hash: Optional[str] = None
    stripe_customer_id: Optional[str] = None  # to connect to Stripe Customer object
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def fetch(id: str, conn: Connection):
        row = await conn.fetchrow(f"SELECT * FROM users WHERE id = '{id}'")
        if row:
            return User.model_validate(dict(row))
        return None

    @staticmethod
    async def fetch_by_email(email: str, db: Connection):
        row = await db.fetchrow("SELECT * FROM users WHERE lower(email) = lower($1)", email)
        if row:
            return User.model_validate(dict(row))
        return None

    @staticmethod
    async def fetch_by_username(username: str, db: Connection):
        row = await db.fetchrow("SELECT * FROM users WHERE lower(username) = lower($1)", username)
        if row:
            return User.model_validate(dict(row))
        return None

    @staticmethod
    async def fetch_by_identifier(identifier: str, db: Connection):
        row = await db.fetchrow(
            """
            SELECT *
            FROM users
            WHERE lower(email) = lower($1)
               OR lower(username) = lower($1)
            """,
            identifier,
        )
        if row:
            return User.model_validate(dict(row))
        return None

    @staticmethod
    async def fetch_by_stripe_id(stripe_id: str, db: Connection):
        row = await db.fetchrow(f"SELECT * FROM users WHERE stripe_customer_id = '{stripe_id}'")
        if row:
            return User.model_validate(dict(row))
        return None

    @staticmethod
    async def create(
        email: str,
        conn: Connection,
        first: str = None,
        last: str = None,
        username: str | None = None,
        password_hash: str | None = None,
    ):
        user = User(email=email, username=username, password_hash=password_hash)
        dump = user.model_dump()
        columns = ",".join(dump.keys())
        values = dump.values()
        place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
        sql = f"INSERT INTO users ({columns}) VALUES ({place_holders})"
        logger.debug(f"Running sql {sql}")
        async with conn.transaction():
            await conn.execute(sql, *values)
        return user

    async def set_basic_auth(self, username: str, password_hash: str, conn: Connection):
        self.username = username
        self.password_hash = password_hash
        self.updated_at = datetime.utcnow()
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE users
                SET username = $1, password_hash = $2, updated_at = $3
                WHERE id = $4
                """,
                self.username,
                self.password_hash,
                self.updated_at,
                self.id,
            )
        return self


# maybe split this out to its own file?
async def auth_user(
    request: Request,
    browser_session: Annotated[str | None, Cookie(alias="session")] = None,
):
    if browser_session is None:
        logger.info("No session found")
        raise HTTPException(status_code=401)

    try:
        claims = decode_auth_token(browser_session)
    except AuthTokenError as error:
        logger.info("Invalid auth token: {}", error)
        raise HTTPException(status_code=401)

    logger.debug("Auth token for user {} is good", claims.user_id)

    return claims.user_id
