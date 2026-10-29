import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("available", [True, False, None])
async def test_health_checks_database_without_authentication(ui_app, monkeypatch, available):
    from everwealth import db

    connection = AsyncMock()
    if available is False:
        connection.fetchval.side_effect = ConnectionError("private database credentials")
    pool = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=connection)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(db, "pool", pool if available is not None else None)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == (200 if available else 503)
    assert response.json() == ({"status": "ok"} if available else {"detail": "Service unavailable"})
    if available is not None:
        pool.acquire.assert_called_once_with(timeout=3)
        connection.fetchval.assert_awaited_once_with("SELECT 1", timeout=3)


@pytest.mark.asyncio
async def test_shutdown_cancels_background_tasks_before_closing_database(monkeypatch):
    from everwealth import db, main

    async def background_job():
        await asyncio.Event().wait()

    tasks = [asyncio.create_task(background_job()) for _ in range(2)]
    pool = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(db, "pool", pool)
    monkeypatch.setattr(db, "lucy_task", tasks[0], raising=False)
    monkeypatch.setattr(db, "rollover_task", tasks[1], raising=False)

    await main.shutdown()

    assert all(task.cancelled() for task in tasks)
    pool.close.assert_awaited_once()
    assert db.pool is None


@pytest.mark.asyncio
async def test_lifespan_cleans_up_on_failure(monkeypatch):
    from everwealth import main

    start = AsyncMock()
    stop = AsyncMock()
    monkeypatch.setattr(main, "startup", start)
    monkeypatch.setattr(main, "shutdown", stop)

    with pytest.raises(RuntimeError):
        async with main.lifespan(main.app):
            raise RuntimeError("request processing failed")

    start.assert_awaited_once()
    stop.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("secure", [True, False])
async def test_login_session_cookie_security(ui_app, monkeypatch, secure):
    from everwealth.auth import web

    monkeypatch.setattr(web.settings, "session_cookie_secure", secure)
    monkeypatch.setattr(
        web.users.User,
        "fetch_by_identifier",
        AsyncMock(return_value=SimpleNamespace(id="test-user", password_hash="password-hash")),
    )
    monkeypatch.setattr(web, "verify_password", lambda *_: True)
    monkeypatch.setattr(
        web.sessions,
        "create",
        AsyncMock(
            return_value=SimpleNamespace(id="session", expiry=datetime.utcnow() + timedelta(days=1))
        ),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="https://test"
    ) as client:
        response = await client.post("/login", data={"identifier": "user", "password": "password"})

    assert response.status_code == 303
    assert ("Secure" in response.headers["set-cookie"]) is secure
    assert "HttpOnly" in response.headers["set-cookie"]
