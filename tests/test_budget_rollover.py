"""Exercise rollover data changes against an isolated SQL database."""

import asyncio
import os
import re
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock

import asyncpg
import pytest

from everwealth.budgets import Budget, BudgetPeriod
from everwealth.budgets.rollover import ensure_current_period, rollover_expired_periods


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_DSN"), reason="Set TEST_POSTGRES_DSN for PostgreSQL checks"
)
async def test_postgres_rollover_parameter_types_and_retry():
    connection = await asyncpg.connect(os.environ["TEST_POSTGRES_DSN"], timeout=5)
    try:
        # Only session-local tables are visible to the application queries below.
        await connection.execute(
            """
            SET search_path TO pg_temp;
            CREATE TEMP TABLE budget_periods (
                id VARCHAR(22) PRIMARY KEY, user_id VARCHAR(22),
                start TIMESTAMP NOT NULL, "end" TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL,
                rollover_completed BOOLEAN NOT NULL DEFAULT FALSE
            );
            CREATE TEMP TABLE budgets (
                id VARCHAR(22) PRIMARY KEY, user_id VARCHAR(22),
                period_id VARCHAR(22), category_id VARCHAR(22), amount INTEGER,
                created_at TIMESTAMP, updated_at TIMESTAMP
            );
        """
        )
        previous = await BudgetPeriod.for_month("test-user", 2026, 10).save(connection)
        await Budget(
            period_id=previous.id, user_id="test-user", category_id="food", amount=500
        ).save(connection)
        current = await BudgetPeriod.for_month("test-user", 2026, 11).save(connection)
        await Budget(
            period_id=current.id, user_id="test-user", category_id="rent", amount=1600
        ).save(connection)
        now = datetime(2026, 11, 4)
        await ensure_current_period("test-user", connection, now)
        await ensure_current_period("test-user", connection, now)
        rows = await connection.fetch(
            "SELECT category_id, amount, created_at FROM budgets WHERE period_id = $1 ORDER BY category_id",
            current.id,
        )
        assert [(row["category_id"], row["amount"]) for row in rows] == [
            ("food", 500),
            ("rent", 1600),
        ]
        assert rows[0]["created_at"] == now
        assert (
            await BudgetPeriod.fetch_for_month("test-user", 2026, 11, connection)
        ).rollover_completed
    finally:
        await connection.close()


class RolloverDatabase:
    """SQLite adapter for the SQL shared with PostgreSQL; no application DB access."""

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE budget_periods (
                id TEXT PRIMARY KEY, user_id TEXT, start TEXT, "end" TEXT,
                created_at TEXT, rollover_completed BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE budgets (
                id TEXT PRIMARY KEY, period_id TEXT, user_id TEXT, category_id TEXT,
                amount INTEGER, rollover BOOLEAN, created_at TEXT, updated_at TEXT
            );
        """
        )
        self.lock_calls = 0

    @asynccontextmanager
    async def transaction(self):
        with self.db:
            yield

    @asynccontextmanager
    async def acquire(self):
        yield self

    def query(self, query, args):
        query = re.sub(r"\$(\d+)", r"?\1", query)
        query = query.replace("EXTRACT(YEAR FROM start)", "CAST(strftime('%Y', start) AS INTEGER)")
        query = query.replace("EXTRACT(MONTH FROM start)", "CAST(strftime('%m', start) AS INTEGER)")
        return self.db.execute(
            query, [arg.isoformat(" ") if isinstance(arg, datetime) else arg for arg in args]
        )

    async def execute(self, query, *args):
        if "pg_advisory_xact_lock" in query:
            self.lock_calls += 1
            return
        self.query(query, args)

    async def fetch(self, query, *args):
        rows = []
        for row in self.query(query, args).fetchall():
            values = dict(row)
            for field in ("start", "end", "created_at"):
                if values.get(field):
                    values[field] = datetime.fromisoformat(values[field])
            rows.append(values)
        return rows

    async def fetchrow(self, query, *args):
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None

    async def period(self, year, month, user="user", completed=False):
        period = await BudgetPeriod.for_month(user, year, month).save(self)
        if completed:
            await self.execute(
                "UPDATE budget_periods SET rollover_completed = TRUE WHERE id = $1", period.id
            )
        return period

    async def budget(self, period, category="food", amount=500, rollover=True):
        await self.execute(
            "INSERT INTO budgets (id, period_id, user_id, category_id, amount, rollover) VALUES ($1,$2,$3,$4,$5,$6)",
            period.id + category,
            period.id,
            period.user_id,
            category,
            amount,
            rollover,
        )

    async def budgets(self, period):
        return await self.fetch(
            "SELECT * FROM budgets WHERE period_id = $1 ORDER BY category_id", period.id
        )


@pytest.fixture
def database():
    database = RolloverDatabase()
    yield database
    database.db.close()


@pytest.mark.asyncio
async def test_page_copies_all_budgets_regardless_of_legacy_rollover_flag(database, monkeypatch):
    from everwealth.budgets import rollover

    old = await database.period(2026, 10)
    await database.budget(old)
    await database.budget(old, "previously-disabled", rollover=False)
    await database.budget(old, "previously-unset", rollover=None)
    # Fix the clock at the shared entry point to test the actual page model call.
    real_ensure = ensure_current_period

    async def fixed_ensure(user, connection):
        return await real_ensure(user, connection, datetime(2026, 11, 1))

    monkeypatch.setattr(rollover, "ensure_current_period", fixed_ensure)
    current = await BudgetPeriod.current("user", database)
    assert current.rollover_completed
    assert [(b["category_id"], b["amount"]) for b in await database.budgets(current)] == [
        ("food", 500),
        ("previously-disabled", 500),
        ("previously-unset", 500),
    ]
    assert len(await database.budgets(old)) == 3
    december = await real_ensure("user", database, datetime(2026, 12, 1))
    assert len(await database.budgets(december)) == 3


@pytest.mark.asyncio
async def test_new_and_edited_budgets_copy_without_any_rollover_option(database):
    october = await database.period(2026, 10)
    await Budget(period_id=october.id, user_id="user", category_id="food", amount=500).save(
        database
    )
    november = await ensure_current_period("user", database, datetime(2026, 11, 1))
    copied = (await database.budgets(november))[0]
    budget = await Budget.fetch(copied["id"], "user", database)
    budget.amount = 650
    await budget.save(database)
    december = await ensure_current_period("user", database, datetime(2026, 12, 1))
    assert [(b["category_id"], b["amount"]) for b in await database.budgets(december)] == [
        ("food", 650)
    ]


@pytest.mark.asyncio
async def test_repairs_preexisting_partial_current_month_without_overwriting(database):
    old = await database.period(2026, 10)
    await database.budget(old)
    await database.budget(old, "rent", 1500)
    current = await database.period(2026, 11)
    await database.budget(current, "rent", 1600)
    await ensure_current_period("user", database, datetime(2026, 11, 3))
    assert [(b["category_id"], b["amount"]) for b in await database.budgets(current)] == [
        ("food", 500),
        ("rent", 1600),
    ]


@pytest.mark.asyncio
async def test_retry_does_not_duplicate_or_resurrect_deleted_budget(database):
    old = await database.period(2026, 10)
    await database.budget(old)
    now = datetime(2026, 11, 1)
    current = await ensure_current_period("user", database, now)
    await ensure_current_period("user", database, now)
    assert len(await database.budgets(current)) == 1
    await database.execute("DELETE FROM budgets WHERE period_id = $1", current.id)
    await ensure_current_period("user", database, now)
    assert await database.budgets(current) == []
    december = await ensure_current_period("user", database, datetime(2026, 12, 1))
    assert await database.budgets(december) == []
    assert database.lock_calls == 4


@pytest.mark.asyncio
async def test_catches_up_all_missed_months_and_legacy_empty_periods(database):
    old = await database.period(2025, 12)
    await database.budget(old)
    await database.period(2026, 1)
    legacy_march = await database.period(2026, 3)
    await database.execute(
        'UPDATE budget_periods SET "end" = $2 WHERE id = $1', legacy_march.id, datetime(2026, 3, 28)
    )
    current = await ensure_current_period("user", database, datetime(2026, 3, 1))
    for month, days in [(1, 31), (2, 28), (3, 31)]:
        period = await BudgetPeriod.fetch_for_month("user", 2026, month, database)
        assert period.end.day == days
        assert period.rollover_completed
        assert len(await database.budgets(period)) == 1
    assert current.start == datetime(2026, 3, 1)
    assert current.end == datetime(2026, 3, 31, 23, 59, 59, 999999)


@pytest.mark.asyncio
async def test_leap_year_and_user_isolation(database):
    old = await database.period(2024, 1)
    await database.budget(old)
    other = await database.period(2024, 1, user="other")
    await database.budget(other, amount=999)
    current = await ensure_current_period("user", database, datetime(2024, 2, 1))
    assert current.end.day == 29
    assert [b["amount"] for b in await database.budgets(current)] == [500]
    assert await BudgetPeriod.fetch_for_month("other", 2024, 2, database) is None


@pytest.mark.asyncio
async def test_first_month_does_not_copy_from_future_period(database):
    future = await database.period(2026, 12)
    await database.budget(future)
    current = await ensure_current_period("user", database, datetime(2026, 11, 1))
    assert current.rollover_completed
    assert await database.budgets(current) == []


@pytest.mark.asyncio
async def test_scheduler_repairs_users_and_continues_after_one_failure(database, monkeypatch):
    from everwealth.budgets import rollover

    await database.period(2026, 10, "broken")
    await database.period(2026, 10, "healthy")
    ensure = AsyncMock(side_effect=[RuntimeError("failure"), None])
    monkeypatch.setattr(rollover, "ensure_current_period", ensure)
    await rollover_expired_periods(database)
    assert [call.args[0] for call in ensure.await_args_list] == ["broken", "healthy"]


@pytest.mark.asyncio
async def test_scheduler_propagates_cancellation(database, monkeypatch):
    from everwealth.budgets import rollover

    await database.period(2026, 10)
    monkeypatch.setattr(
        rollover, "ensure_current_period", AsyncMock(side_effect=asyncio.CancelledError)
    )
    with pytest.raises(asyncio.CancelledError):
        await rollover_expired_periods(database)


@pytest.mark.asyncio
async def test_failed_copy_rolls_back_and_can_be_retried(database, monkeypatch):
    old = await database.period(2026, 10)
    await database.budget(old)
    database.db.commit()
    execute = database.execute

    async def fail_marking_complete(query, *args):
        if "SET rollover_completed = TRUE" in query:
            raise RuntimeError("interrupted")
        return await execute(query, *args)

    monkeypatch.setattr(database, "execute", fail_marking_complete)
    now = datetime(2026, 11, 1)
    with pytest.raises(RuntimeError, match="interrupted"):
        await ensure_current_period("user", database, now)
    assert await BudgetPeriod.fetch_for_month("user", 2026, 11, database) is None
    monkeypatch.setattr(database, "execute", execute)
    current = await ensure_current_period("user", database, now)
    assert len(await database.budgets(current)) == 1
