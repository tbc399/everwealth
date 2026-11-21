from datetime import datetime
import re
from unittest.mock import AsyncMock

import httpx
import pytest

from everwealth.budgets import Budget, BudgetOverview, BudgetPeriod, BudgetView


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/budgets", "/budgets/partial"])
async def test_month_selection_and_status_colors(ui_app, monkeypatch, path):
    period = BudgetPeriod.for_month("test-user", 2026, 1)
    lookup = AsyncMock(return_value=period)
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", lookup)
    monkeypatch.setattr(BudgetPeriod, "timeline", AsyncMock(return_value=[
        {"start": datetime(2026, 1, 1), "income": 10000, "spending": 11000},
        {"start": datetime(2025, 12, 1), "income": 10000, "spending": 10000},
        {"start": datetime(2026, 3, 1), "income": 0, "spending": 0},
    ]))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get(path, params={"month": "2026-01"})
    assert response.status_code == 200
    assert "January 2026" in response.text
    assert 'value="2026-01" selected' in response.text
    assert 'hx-get="/budgets/partial" hx-trigger="change"' in response.text
    assert 'aria-label="January 2026: spending exceeded income"' in response.text
    assert response.text.count("month-over-income") == 1
    assert response.text.count("month-within-income") == 2
    assert 'hx-get="/budgets/create?month=2026-01"' in response.text
    assert 'hx-get="/budgets/income/edit?month=2026-01"' in response.text
    assert BudgetView.fetch_all_by_month.call_args.args[1:3] == (2026, 1)
    assert BudgetOverview.fetch.call_args.args[1] == period
    assert lookup.call_args.args[:3] == ("test-user", 2026, 1)
    if path.endswith("partial"):
        assert "<html" not in response.text
        assert response.headers["HX-Push-Url"] == "/budgets?month=2026-01"

    header = response.text.split('<header class="page-header">', 1)[1].split("</header>", 1)[0]
    assert 'aria-label="Budget month navigation"' in header
    assert "<button" not in header
    assert re.findall(r'<option value="([^"]+)"', header) == ["2026-03", "2026-01", "2025-12"]
    assert "New budget" not in header
    assert "Categories" not in header
    list_header = response.text.split('<div class="panel-header">', 1)[1].split('<div class="overflow-x-auto">', 1)[0]
    assert "New budget" in list_header
    assert "Categories" in list_header
    summary = response.text.split('aria-label="Monthly budget overview">', 1)[1].split("</section>", 1)[0]
    assert summary.index("Left to spend") < summary.index("Income") < summary.index("Spending")


@pytest.mark.asyncio
async def test_selector_keeps_current_month_without_timeline_entries(ui_app, monkeypatch):
    monkeypatch.setattr(BudgetPeriod, "timeline", AsyncMock(return_value=[]))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get("/budgets/partial")
    assert response.status_code == 200
    assert 'value="2026-10" selected>October 2026</option>' in response.text
    assert response.headers["HX-Push-Url"] == "/budgets?month=2026-10"


@pytest.mark.asyncio
@pytest.mark.parametrize("month, status", [("bad", 422), ("2026-13", 422), ("0000-01", 422), ("2020-01", 404)])
async def test_invalid_or_unavailable_month(ui_app, monkeypatch, month, status):
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", AsyncMock(return_value=None))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get("/budgets/partial", params={"month": month})
    assert response.status_code == status


@pytest.mark.asyncio
async def test_create_budget_uses_selected_month(ui_app, monkeypatch):
    from everwealth.budgets import Category
    from everwealth.db import get_connection

    period = BudgetPeriod.for_month("test-user", 2026, 1)
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", AsyncMock(return_value=period))
    monkeypatch.setattr(Category, "fetch", AsyncMock(return_value=object()))
    connection = ui_app.dependency_overrides[get_connection]()
    db = await anext(connection)
    await connection.aclose()
    db.fetchrow.return_value = None
    saved = []

    async def save(budget, connection):
        saved.append(budget)

    monkeypatch.setattr(Budget, "save", save)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        modal = await client.get("/budgets/create?month=2026-01")
        response = await client.post("/budgets", data={"category": "groceries", "amount": 500, "month": "2026-01"})
    assert 'name="month" value="2026-01"' in modal.text
    assert saved[0].period_id == period.id
    assert response.headers["location"] == "/budgets?month=2026-01"


@pytest.mark.asyncio
async def test_income_editor_and_save_keep_selected_month(ui_app, monkeypatch):
    from everwealth.budgets import Category
    from everwealth.db import get_connection

    period = BudgetPeriod.for_month("test-user", 2026, 1)
    monkeypatch.setattr(BudgetPeriod, "fetch_for_month", AsyncMock(return_value=period))
    monkeypatch.setattr(Category, "fetch_many", AsyncMock(return_value=[
        Category(id="income", name="Income", type="income", user_id="test-user"),
    ]))
    budget = Budget(id="income-plan", period_id=period.id, user_id="test-user", category_id="income", amount=5000)
    monkeypatch.setattr(Budget, "fetch", AsyncMock(return_value=budget))
    save = AsyncMock()
    monkeypatch.setattr(Budget, "save", save)
    connection = ui_app.dependency_overrides[get_connection]()
    db = await anext(connection)
    await connection.aclose()
    db.fetch.return_value = [{"id": budget.id, "category_id": "income", "amount": 5000}]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        modal = await client.get("/budgets/income/edit?month=2026-01")
        response = await client.put("/budgets/income-plan", data={"amount": 6000, "month": "2026-01"})
        deleted = await client.delete("/budgets/income-plan?month=2026-01")
    assert 'name="month" value="2026-01"' in modal.text
    assert "January 2026" in modal.text
    assert db.fetch.call_args.args[1:] == ("test-user", period.id)
    save.assert_awaited_once()
    assert budget.amount == 6000
    assert response.headers["HX-Redirect"] == "/budgets?month=2026-01"
    assert deleted.headers["HX-Redirect"] == "/budgets?month=2026-01"
