import re
from datetime import date
from html import unescape
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from everwealth.transactions import Transaction
from everwealth.transactions.web import _month_bounds, _month_options


@pytest.mark.parametrize(
    "month, start, end",
    [
        ("", None, None),
        ("2024-02", date(2024, 2, 1), date(2024, 3, 1)),
        ("2025-12", date(2025, 12, 1), date(2026, 1, 1)),
    ],
)
def test_calendar_month_bounds(month, start, end):
    assert _month_bounds(month) == (start, end)


def test_month_options_include_inactive_months_and_selected_empty_periods():
    months = _month_options(date(2025, 11, 20), date(2026, 2, 10), date(2025, 10, 1))
    values = [item["value"] for item in months]
    assert values == sorted(values, reverse=True)
    assert {"2025-10", "2025-11", "2025-12", "2026-01", "2026-02"} <= set(values)
    assert next(item["label"] for item in months if item["value"] == "2025-12") == "December 2025"


def test_empty_history_still_offers_current_month():
    assert _month_options(None, None, None) == [
        {"value": date.today().isoformat()[:7], "label": date.today().strftime("%B %Y")}
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/transactions",
        "/transactions/partial",
        "/transactions/transactions-tab",
    ],
)
async def test_month_search_and_account_filters_combine(ui_app, path):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(
            path,
            params={
                "month": "2026-10",
                "q": "  fOoDs  ",
                "account": "checking",
            },
            headers={"HX-Request": "true"},
        )
    assert response.status_code == 200
    assert len(re.findall(r'<tr id="tran_', response.text)) == 8
    assert "Monthly payroll" not in response.text
    assert "City Coffee" not in response.text
    assert 'value="2026-10" selected' in response.text
    assert 'name="q" value="fOoDs"' in response.text


@pytest.mark.asyncio
async def test_blank_account_and_search_return_unfiltered_results(ui_app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/transactions/transactions-tab?account=&month=&q=+++",
            headers={"HX-Request": "true"},
        )
    assert response.status_code == 200
    assert response.headers["HX-Push-Url"] == "/transactions?page=1"
    assert "55 transactions" in response.text


@pytest.mark.asyncio
async def test_filtered_pagination_uses_counts_and_preserves_encoded_filters(ui_app, monkeypatch):
    monkeypatch.setattr(Transaction, "count_many", AsyncMock(return_value=101))
    fetch = AsyncMock(return_value=[])
    monkeypatch.setattr(Transaction, "fetch_many", fetch)
    search = "A&B + 50%_"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/transactions/transactions-tab",
            params={
                "account": "checking",
                "month": "2024-02",
                "q": f" {search} ",
                "page": 2,
            },
            headers={"HX-Request": "true"},
        )
    assert response.status_code == 200
    expected = {"account": ["checking"], "month": ["2024-02"], "q": [search]}
    pushed = parse_qs(urlsplit(response.headers["HX-Push-Url"]).query)
    assert pushed == {"page": ["2"], **expected}
    for url in re.findall(r'hx-get="(/transactions/transactions-tab\?[^"]+)"', response.text):
        query = parse_qs(urlsplit(unescape(url)).query)
        assert {key: query[key] for key in expected} == expected
    assert fetch.await_args.kwargs == {
        "limit": 50,
        "offset": 50,
        "start_date": date(2024, 2, 1),
        "end_date": date(2024, 3, 1),
        "search": search,
    }


@pytest.mark.asyncio
async def test_empty_month_clamps_pagination_and_keeps_filters_available(ui_app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/transactions/transactions-tab?month=2020-01&page=50", headers={"HX-Request": "true"}
        )
    assert response.status_code == 200
    assert "No transactions found." in response.text
    assert "Showing 0&ndash;0 of 0" in response.text
    assert 'value="2020-01" selected' in response.text
    assert 'aria-label="Clear filters"' in response.text
    assert response.headers["HX-Push-Url"] == "/transactions?page=1&month=2020-01"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params",
    [
        {"month": "2026-13"},
        {"month": "0000-01"},
        {"month": "2026-2"},
        {"month": "2026-01-01"},
        {"q": "a" * 201},
    ],
)
async def test_invalid_filter_values_are_rejected(ui_app, params):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.get("/transactions", params=params)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_database_queries_bind_filters_and_scope_to_user():
    db = AsyncMock()
    db.fetch.return_value = []
    db.fetchval.return_value = 0
    search = "%_'; SELECT pg_sleep(10); --"
    filters = {"start_date": date(2024, 2, 1), "end_date": date(2024, 3, 1), "search": search}
    await Transaction.fetch_many("user-a", db, "account-a", limit=50, offset=50, **filters)
    await Transaction.count_many("user-a", db, "account-a", **filters)
    fetch_sql, *fetch_args = db.fetch.await_args.args
    count_sql, *count_args = db.fetchval.await_args.args
    assert fetch_args == ["user-a", "account-a", 50, 50, *filters.values()]
    assert count_args == ["user-a", "account-a", *filters.values()]
    for sql in (fetch_sql, count_sql):
        assert "t.user_id = $1" in sql
        assert "COALESCE(t.hidden, FALSE) = FALSE" in sql
        assert "strpos(lower(t.description)" in sql
        assert search not in sql
