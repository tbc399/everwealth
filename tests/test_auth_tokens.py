from datetime import datetime, timedelta

import pytest

from everwealth.auth.tokens import AuthTokenError, create_auth_token, decode_auth_token


def test_auth_token_round_trip():
    token = create_auth_token(
        "user_123",
        session_id="session_123",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        secret="test-secret",
    )

    claims = decode_auth_token(token, secret="test-secret")

    assert claims.user_id == "user_123"
    assert claims.sid == "session_123"


def test_auth_token_rejects_bad_signature():
    token = create_auth_token(
        "user_123",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        secret="test-secret",
    )

    with pytest.raises(AuthTokenError):
        decode_auth_token(token, secret="different-secret")


def test_auth_token_rejects_expired_token():
    token = create_auth_token(
        "user_123",
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        secret="test-secret",
    )

    with pytest.raises(AuthTokenError):
        decode_auth_token(token, secret="test-secret")
