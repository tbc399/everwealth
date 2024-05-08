from starlette.middleware.authentication import AuthenticationBackend
from fastapi.exceptions import HTTPException
from starlette.requests import HTTPConnection
from starlette.authentication import AuthCredentials
from everwealth.auth import sessions, users, User
from fastapi import Cookie
from loguru import logger


class SessionBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if "session" not in conn.cookies:
            logger.info()
            return

        from everwealth.db import pool

        async with pool.acquire() as db:
            # TODO: should user and session be wrapped into one to save on db access? Maybe through signed sessions?
            session_id = conn.cookies["session"]
            session: sessions.Session = await sessions.fetch(session_id, db)
            # TODO: bypass for now
            # if not session or session.is_expired():
            #    logger.info(f"Session {session_id} does not exist or is no longer valid")
            #    raise HTTPException(status_code=401)

            user = await users.fetch(session.user_id, db)
            logger.debug(f"User {user.id} found")

        return AuthCredentials(["authenticated"]), user
