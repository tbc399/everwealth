import re
from unittest.mock import AsyncMock

import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_id", ["", "income"])
async def test_create_main_or_subcategory(ui_app, monkeypatch, parent_id):
    from everwealth.budgets import Category
    from everwealth.budgets.models.categories import CategoryType

    parent = Category(id="income", name="Income", type="income", user_id="test-user")
    fetch = AsyncMock(return_value=parent)
    create = AsyncMock()
    monkeypatch.setattr(Category, "fetch", fetch)
    monkeypatch.setattr(Category, "create", create)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        page = await client.get("/categories")
        response = await client.post("/categories", data={"name": " Salary ", "parent_id": parent_id})
    assert 'name="parent_id"' in page.text
    assert 'Subcategory of Food &amp; dining' in page.text
    assert 'value="groceries"' not in page.text
    assert response.status_code == 303
    assert create.call_args.args[:2] == ("Salary", "test-user")
    assert create.call_args.kwargs == {
        "type": "income" if parent_id else CategoryType.expense,
        "parent_id": parent_id or None,
    }
    if parent_id:
        fetch.assert_awaited_once_with(parent_id, "test-user", create.call_args.args[2])
    else:
        fetch.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("case, status", [("missing", 400), ("nested", 400), ("blank", 422), ("duplicate", 409)])
async def test_reject_invalid_category_creation(ui_app, monkeypatch, case, status):
    from everwealth.budgets import Category

    parent = Category(id="parent", name="Parent", parent_id="root", user_id="test-user")
    monkeypatch.setattr(Category, "fetch", AsyncMock(return_value=parent if case == "nested" else None))
    create = AsyncMock()
    monkeypatch.setattr(Category, "create", create)
    data = {"name": "New", "parent_id": "parent"}
    if case == "blank":
        data = {"name": "   "}
    elif case == "duplicate":
        data = {"name": " groceries "}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.post("/categories", data=data)
    assert response.status_code == status
    create.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("has_budget", [False, True])
async def test_planned_income_editor(ui_app, monkeypatch, has_budget):
    from everwealth.budgets import BudgetView, Category

    categories = [
        Category(id="income", name="Income", type="income", user_id="test-user"),
        Category(id="salary", name="Salary", type="income", parent_id="income", user_id="test-user"),
        Category(id="bonus", name="Bonus", type="income", parent_id="income", user_id="test-user"),
        Category(id="food", name="Food", type="expense", user_id="test-user"),
    ]
    monkeypatch.setattr(Category, "fetch_many", AsyncMock(return_value=categories))
    monkeypatch.setattr(BudgetView, "fetch_all_by_month", AsyncMock(return_value=[
        BudgetView(id="income-budget", user_id="test-user", category_id="income",
                   category_name="Income", amount=5000, transactions_total=0),
    ] if has_budget else []))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        page = await client.get("/budgets")
        response = await client.get("/budgets/income/edit")
        for method, path in (("post", "/budgets"), ("put", "/budgets/salary-budget")):
            invalid = await client.request(method, path, data={"category": "salary", "amount": -1})
            assert invalid.status_code == 422

    assert 'aria-label="Edit planned income"' in page.text
    assert response.status_code == 200
    if has_budget:
        assert 'hx-put="/budgets/income-budget"' in response.text
        assert 'value="5000"' in response.text
    else:
        assert 'action="/budgets" method="post"' in response.text
    assert response.text.count('name="amount"') == 1
    assert 'value="income"' in response.text
    assert 'value="salary"' not in response.text
    assert 'value="bonus"' not in response.text
    assert 'value="food"' not in response.text


@pytest.mark.asyncio
async def test_create_manual_account(ui_app, monkeypatch):
    from everwealth.accounts.models import Account

    save = AsyncMock()
    monkeypatch.setattr(Account, "save", save)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.post("/accounts", data={"name": "  My checking  "})
        for name in ("", "   ", "x" * 101):
            invalid = await client.post("/accounts", data={"name": name})
            assert invalid.status_code == 422

    assert response.status_code == 303
    assert response.headers["location"] == "/accounts"
    save.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_account_is_saved_for_authenticated_user(ui_app):
    from everwealth.db import get_connection

    connection = ui_app.dependency_overrides[get_connection]()
    db = await anext(connection)
    await connection.aclose()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.post("/accounts", data={"name": "  My checking  "})
    assert response.status_code == 303
    args = db.execute.call_args.args
    assert args[2:6] == ("My checking", "manual", "other", "test-user")
    assert args[8:11] == (None, None, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path, heading",
    [
        ("/dashboard", "Overview"),
        ("/budgets", "Budgets"),
        ("/categories", "Categories"),
        ("/transactions", "Transactions"),
        ("/transactions/rules", "Transactions"),
        ("/accounts", "Accounts"),
        ("/accounts/assets", "Accounts"),
        ("/settings/profile", "Settings"),
    ],
)
async def test_pages_keep_one_shared_shell(ui_app, path, heading):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(path)

    assert response.status_code == 200
    assert len(re.findall(r'id="main-content"', response.text)) == 1
    assert '<h1 class="page-heading">' + heading + "</h1>" in response.text
    assert 'aria-label="Primary navigation"' in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/dashboard/partial",
        "/budgets/partial",
        "/categories/partial",
        "/transactions/partial",
        "/transactions/rules-tab",
        "/accounts/partial",
        "/accounts/assets/partial",
        "/settings/partial",
    ],
)
async def test_navigation_partials_do_not_duplicate_the_shell(ui_app, path):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(path, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "<h1" in response.text
    assert "<html" not in response.text
    assert 'id="main-content"' not in response.text
    assert "hx-swap-oob" not in response.text


@pytest.mark.asyncio
async def test_account_filter_history_uses_the_public_page_url(ui_app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/transactions/transactions-tab?page=2&account=checking",
            headers={"HX-Request": "true"},
        )
    assert response.headers["HX-Push-Url"] == "/transactions?page=2&account=checking"
    assert "Showing 51" in response.text


@pytest.mark.asyncio
async def test_inline_editor_is_a_valid_table_fragment(ui_app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        edit = await client.get("/transactions/0/edit")
        saved = await client.put(
            "/transactions/0",
            data={
                "description": "Whole Foods Market",
                "date": "2026-10-22",
                "notes": "Weekly groceries",
                "category": "groceries",
            },
        )
    assert edit.text.lstrip().startswith("<tr")
    assert '<td colspan="5"' in edit.text
    assert saved.status_code == 200
    assert saved.text.lstrip().startswith("<tr")
    assert "-$86.42" in saved.text or "&minus;$86.42" in saved.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/budgets/create", "/budgets/0/edit", "/transactions/upload"])
async def test_dialogs_have_native_backdrop_and_close_controls(ui_app, path):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(path)
    assert response.status_code == 200
    assert "<dialog" in response.text
    assert 'method="dialog" class="modal-backdrop"' in response.text
    assert "data-close-modal" in response.text


@pytest.mark.asyncio
async def test_overview_requires_authentication(ui_app):
    from everwealth.auth import auth_user

    override = ui_app.dependency_overrides.pop(auth_user)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
        ) as client:
            page = await client.get("/dashboard")
            partial = await client.get("/dashboard/partial", headers={"HX-Request": "true"})
        assert page.status_code == 303
        assert page.headers["location"] == "/login"
        assert partial.headers["HX-Redirect"] == "/login"
        assert "Recent transactions" not in partial.text
    finally:
        ui_app.dependency_overrides[auth_user] = override


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path, destination",
    [
        ("/budgets/0", "/budgets"),
        ("/accounts/checking", "/accounts"),
    ],
)
async def test_delete_refreshes_the_page(ui_app, path, destination):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.delete(path)
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == destination
