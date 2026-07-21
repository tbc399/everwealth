import base64
import binascii
import hashlib
import hmac
import json
from datetime import datetime, timedelta, UTC
from typing import Any

from pydantic import BaseModel, ValidationError


class AuthTokenError(ValueError):
    pass


class AuthTokenClaims(BaseModel):
    sub: str
    sid: str | None = None
    iat: int
    exp: int

    @property
    def user_id(self) -> str:
        return self.sub


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (binascii.Error, ValueError) as error:
        raise AuthTokenError("Invalid token encoding") from error


def _json_encode(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _signing_secret(secret: str | None = None) -> str:
    if secret:
        return secret

    from everwealth.config import settings

    if settings.auth_token_secret:
        return settings.auth_token_secret

    return settings.database_url


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def create_auth_token(
    user_id: str,
    session_id: str | None = None,
    expires_at: datetime | None = None,
    secret: str | None = None,
) -> str:
    now = datetime.now(UTC)
    expiry = expires_at or now + timedelta(days=10)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "sid": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
    }
    encoded_header = _base64url_encode(_json_encode(header))
    encoded_payload = _base64url_encode(_json_encode(payload))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input, _signing_secret(secret))
    return f"{signing_input}.{signature}"


def decode_auth_token(token: str, secret: str | None = None) -> AuthTokenClaims:
    try:
        encoded_header, encoded_payload, signature = token.split(".")
    except ValueError as error:
        raise AuthTokenError("Malformed token") from error

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = _sign(signing_input, _signing_secret(secret))
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthTokenError("Invalid token signature")

    try:
        header = json.loads(_base64url_decode(encoded_header))
        payload = json.loads(_base64url_decode(encoded_payload))
    except json.JSONDecodeError as error:
        raise AuthTokenError("Invalid token payload") from error

    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise AuthTokenError("Unsupported token header")

    try:
        claims = AuthTokenClaims.model_validate(payload)
    except ValidationError as error:
        raise AuthTokenError("Invalid token claims") from error
    if claims.exp < int(datetime.utcnow().timestamp()):
        raise AuthTokenError("Expired token")

    return claims
