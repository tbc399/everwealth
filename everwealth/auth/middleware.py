from fastapi.exceptions import HTTPException
from loguru import logger
from starlette.authentication import AuthCredentials, BaseUser
from starlette.middleware.authentication import AuthenticationBackend
from starlette.requests import HTTPConnection

from everwealth.auth.tokens import AuthTokenError, decode_auth_token


class TokenUser(BaseUser):
    def __init__(self, user_id: str):
        self.id = user_id

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.id


class SessionBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if "session" not in conn.cookies:
            return

        try:
            claims = decode_auth_token(conn.cookies["session"])
        except AuthTokenError as error:
            logger.info("Invalid auth token: {}", error)
            raise HTTPException(status_code=401)

        return AuthCredentials(["authenticated"]), TokenUser(claims.user_id)
