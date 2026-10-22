import re

import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path, heading",
    [
        ("/dashboard", "Overview"),
        ("/budgets", "Budgets"),
        ("/categories", "Categories"),
        ("/transactions", "Transactions"),
        ("/transactions/rules", "Transactions"),
        ("/accounts", "Connections"),
        ("/accounts/assets", "Connections"),
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
