from starlette.middleware.authentication import AuthenticationBackend
from fastapi.exceptions import HTTPException
from starlette.requests import HTTPConnection
from starlette.authentication import AuthCredentials
from everwealth.users import User


class SessionBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if "session" not in conn.cookies:
            return

        session_id = conn.cookies["session"]


        return AuthCredentials(["authenticated"]), User(username)
