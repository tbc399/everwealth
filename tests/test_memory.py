import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from everwealth import memory


def test_resident_bytes_uses_resident_pages(monkeypatch):
    monkeypatch.setattr(Path, "read_text", lambda self: "1000 250 0 0 0 0 0")
    monkeypatch.setattr(memory.os, "sysconf", lambda key: 4096)
    assert memory.resident_bytes() == 250 * 4096


@pytest.mark.parametrize("contents", ["", "invalid invalid"])
def test_unavailable_memory_metrics_are_optional(monkeypatch, contents):
    monkeypatch.setattr(Path, "read_text", lambda self: contents)
    assert memory.resident_bytes() is None


def test_release_collects_before_trimming(monkeypatch):
    calls = []
    collect = Mock(side_effect=lambda: calls.append("collect"))
    trim = Mock(side_effect=lambda pad: calls.append("trim"))
    monkeypatch.setattr(memory.gc, "collect", collect)
    monkeypatch.setattr(memory.sys, "platform", "linux")
    monkeypatch.setattr(memory, "log_memory", Mock())
    monkeypatch.setattr(memory.ctypes, "CDLL", lambda name: SimpleNamespace(malloc_trim=trim))
    memory.release_memory()
    assert calls == ["collect", "trim"]
    trim.assert_called_once_with(0)
    assert trim.argtypes == [memory.ctypes.c_size_t]
    assert trim.restype == memory.ctypes.c_int


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_cleanup_works_without_malloc_trim(monkeypatch, platform):
    collect = Mock()
    monkeypatch.setattr(memory.gc, "collect", collect)
    monkeypatch.setattr(memory.sys, "platform", platform)
    monkeypatch.setattr(memory, "log_memory", Mock())
    monkeypatch.setattr(memory.ctypes, "CDLL", lambda name: SimpleNamespace())
    memory.release_memory()
    collect.assert_called_once()


@pytest.mark.asyncio
async def test_startup_uses_small_pool_and_retains_background_jobs(monkeypatch):
    from everwealth import db, main

    async def job(*args):
        await asyncio.Event().wait()

    pool = SimpleNamespace(close=AsyncMock())
    create = AsyncMock(return_value=pool)
    monkeypatch.setattr(main.asyncpg, "create_pool", create)
    monkeypatch.setattr(main.lucy, "run", job)
    monkeypatch.setattr(main, "run_rollover_scheduler", job)
    monkeypatch.setattr(main, "log_memory", Mock())
    monkeypatch.setattr(db, "pool", None)
    monkeypatch.setattr(db, "lucy_task", None, raising=False)
    monkeypatch.setattr(db, "rollover_task", None, raising=False)
    await main.startup()
    try:
        assert create.call_args.kwargs == {
            "min_size": 0, "max_size": 4, "max_inactive_connection_lifetime": 60,
        }
        assert not db.lucy_task.done()
        assert not db.rollover_task.done()
    finally:
        await main.shutdown()
    pool.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_successful_import_schedules_cleanup(ui_app, monkeypatch):
    from everwealth.transactions import web

    cleanup = AsyncMock()
    monkeypatch.setattr(web, "release_memory", cleanup)
    monkeypatch.setattr(web.Transaction, "create_many", AsyncMock())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.post("/transactions/upload", data={"account": "checking"}, files={
            "file": ("data.csv", b"Date,Description,Amount\n2026-11-09,Coffee,-4.50\n"),
        })
    assert response.status_code == 303
    cleanup.assert_awaited_once()
