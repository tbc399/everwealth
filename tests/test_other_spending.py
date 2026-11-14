import re
import sqlite3
from unittest.mock import AsyncMock

import httpx
import pytest

from everwealth.budgets import BudgetOverview, BudgetPeriod
from everwealth.transactions import Transaction


@pytest.mark.asyncio
@pytest.mark.parametrize("add_budget, expected", [(False, 35.34), (True, 15.34)])
async def test_other_spending_respects_period_budgets_and_transaction_filters(add_budget, expected):
    with sqlite3.connect(":memory:") as sql:
        sql.row_factory = sqlite3.Row
        sql.executescript("""
            CREATE TABLE categories (id TEXT, name TEXT, type TEXT, parent_id TEXT);
            CREATE TABLE budgets (user_id TEXT, period_id TEXT, category_id TEXT, amount INTEGER);
            CREATE TABLE transactions (user_id TEXT, category_id TEXT, amount INTEGER, date TEXT, hidden BOOLEAN,
                id TEXT, description TEXT DEFAULT 'Purchase');
            INSERT INTO categories VALUES ('food', 'Food', 'expense', NULL),
                ('misc', 'Misc', 'expense', NULL), ('travel', 'Travel', 'expense', NULL),
                ('income', 'Income', 'income', NULL);
            INSERT INTO budgets VALUES ('user', 'period', 'food', 0),
                ('user', 'old-period', 'misc', 500), ('other-user', 'period', 'travel', 500);
            INSERT INTO transactions (user_id, category_id, amount, date, hidden) VALUES
                ('user', 'food', -2000, '2026-11-01', 0),
                ('user', NULL, -1234, '2026-11-01', NULL),
                ('user', 'misc', -2000, '2026-11-30', 0),
                ('user', 'travel', -300, '2026-11-15', 0),
                ('user', 'misc', -100000, '2026-11-15', 1),
                ('user', 'income', 500000, '2026-11-15', 0),
                ('other-user', 'misc', -9000, '2026-11-15', 0),
                ('user', 'misc', -9000, '2026-10-31', 0),
                ('user', 'misc', -9000, '2026-12-01', 0);
        """)
        sql.execute("UPDATE transactions SET id = CAST(rowid AS TEXT)")
        if add_budget:
            sql.execute("INSERT INTO budgets VALUES ('user', 'period', 'misc', 100)")

        async def fetchrow(query, *args):
            query = re.sub(r"(\$\d+)::date", r"date(\1)", query)
            params = {str(i): value for i, value in enumerate(args, 1)}
            return dict(sql.execute(query, params).fetchone())

        db = AsyncMock()
        db.fetchrow.side_effect = fetchrow

        async def fetch(query, *args):
            params = {str(i): value for i, value in enumerate(args, 1)}
            return [dict(row) for row in sql.execute(query, params).fetchall()]

        db.fetch.side_effect = fetch
        period = BudgetPeriod.for_month("user", 2026, 11)
        period.id = "period"
        overview = await BudgetOverview.fetch("user", period, db)
        assert overview.other_spending == expected
        assert overview.current_spend == 55.34
        assert overview.current_income == 5000
        details = await Transaction.fetch_other_spending(
            "user", period.id, period.start.date(), period.end.date(), db,
        )
        assert sum(abs(item.amount) for item in details) == round(expected * 100)
        assert [item.category_name for item in details] == (
            ["Travel", None] if add_budget else ["Misc", "Travel", None]
        )
        sql.execute("DELETE FROM transactions")
        empty = await BudgetOverview.fetch("user", period, db)
        assert empty.other_spending == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/budgets", "/budgets/partial?month=2026-01"])
async def test_other_spending_is_a_summary_row(ui_app, monkeypatch, path):
    overview = BudgetOverview(other_spending=1234, current_spend=2410, expected_spend=2750)
    monkeypatch.setattr(BudgetOverview, "fetch", AsyncMock(return_value=overview))
    period = BudgetPeriod.for_month("test-user", 2026, 1)
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", AsyncMock(return_value=period))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get(path)
    assert response.status_code == 200
    row = response.text.split('<tr id="other-spending">')[1].split("</tr>")[0]
    assert "Other spending" in row
    assert "$1,234" in row
    assert "Not budgeted" in row
    assert 'hx-get="/budgets/other-spending?month=' in row
    assert 'hx-target="body"' in row
    assert "5 categories" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("empty", [False, True])
async def test_other_spending_dialog_shows_categories_for_selected_month(ui_app, monkeypatch, empty):
    period = BudgetPeriod.for_month("test-user", 2026, 1)
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", AsyncMock(return_value=period))
    transactions = [] if empty else [
        Transaction(user_id="test-user", description="Coffee", amount=-1234,
                    date=period.start.date(), category_name="Dining"),
        Transaction(user_id="test-user", description="Shop", amount=-500,
                    date=period.start.date()),
    ]
    fetch = AsyncMock(return_value=transactions)
    monkeypatch.setattr(Transaction, "fetch_other_spending", fetch)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get("/budgets/other-spending?month=2026-01")
    assert response.status_code == 200
    assert '<dialog id="other-spending-detail"' in response.text
    assert "January 2026" in response.text
    assert "<html" not in response.text
    assert fetch.call_args.args[:4] == (
        "test-user", period.id, period.start.date(), period.end.date(),
    )
    if empty:
        assert "No other spending for this month." in response.text
        assert "$0.00 total" in response.text
    else:
        assert "Coffee" in response.text
        assert "Dining" in response.text
        assert "Uncategorized" in response.text
        assert "$17.34 total" in response.text
        assert "$12.34" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("month, status", [("invalid", 422), ("2020-01", 404)])
async def test_other_spending_dialog_rejects_invalid_or_unavailable_period(ui_app, monkeypatch, month, status):
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", AsyncMock(return_value=None))
    fetch = AsyncMock()
    monkeypatch.setattr(Transaction, "fetch_other_spending", fetch)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get("/budgets/other-spending", params={"month": month})
    assert response.status_code == status
    fetch.assert_not_awaited()
