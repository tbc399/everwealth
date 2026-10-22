import os
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/everwealth_test")
os.environ.setdefault("PLAID_CLIENT_ID", "test-client")
os.environ.setdefault("PLAID_SECRET", "test-secret")
os.environ.setdefault("PLAID_WEBHOOK_HANDLER_URL", "https://example.com/plaid")


@pytest.fixture
def ui_app(monkeypatch):
    from everwealth.accounts.models import Account, Asset
    from everwealth.auth import auth_user
    from everwealth.budgets import BudgetOverview, BudgetPeriod, BudgetView, Category
    from everwealth.db import get_connection
    from everwealth.main import app
    from everwealth.transactions import Transaction
    from everwealth.web import settings

    period = BudgetPeriod.for_month("test-user", 2026, 10)
    categories = [
        Category(id="food", name="Food & dining", user_id="test-user"),
        Category(id="groceries", name="Groceries", user_id="test-user", parent_id="food"),
    ]
    accounts = [
        Account(
            id="checking",
            name="Everyday checking",
            type="cash",
            user_id="test-user",
            institution_name="First Bank",
            last4="4821",
            last_sync=datetime.utcnow(),
        ),
        Account(
            id="credit",
            name="Rewards card",
            type="credit",
            user_id="test-user",
            institution_name="Capital Bank",
            last4="9012",
            last_sync=datetime.utcnow(),
        ),
    ]
    budgets = [
        BudgetView(
            id=str(index),
            user_id="test-user",
            category_id="groceries",
            category_name=name,
            amount=amount,
            transactions_total=spent,
            rollover=True,
        )
        for index, (name, amount, spent) in enumerate(
            [
                ("Groceries", 650, -428),
                ("Restaurants", 250, -286),
                ("Transport", 200, -132),
                ("Utilities", 300, -214),
                ("Housing", 1350, -1350),
            ]
        )
    ]
    transactions = [
        Transaction(
            id=str(index),
            user_id="test-user",
            account_id="checking",
            description=["Whole Foods Market", "Monthly payroll", "City Coffee"][index % 3],
            amount=[-8642, 480000, -650][index % 3],
            date=date(2026, 10, 22) - timedelta(days=index),
            category_id="groceries",
            category_name="Groceries",
        )
        for index in range(55)
    ]

    async def transaction_page(user_id, db, account_id=None, limit=None, offset=0):
        return transactions[offset : offset + limit if limit is not None else None]

    monkeypatch.setattr(BudgetPeriod, "current", AsyncMock(return_value=period))
    monkeypatch.setattr(
        BudgetOverview,
        "fetch",
        AsyncMock(
            return_value=BudgetOverview(
                current_income=4800,
                expected_income=5200,
                current_spend=2410,
                expected_spend=2750,
            )
        ),
    )
    monkeypatch.setattr(BudgetView, "fetch_all_by_month", AsyncMock(return_value=budgets))
    monkeypatch.setattr(BudgetView, "fetch", AsyncMock(return_value=budgets[0]))
    monkeypatch.setattr(Category, "fetch_many", AsyncMock(return_value=categories))
    monkeypatch.setattr(Category, "fetch", AsyncMock(return_value=categories[1]))
    monkeypatch.setattr(Transaction, "fetch_many", transaction_page)
    monkeypatch.setattr(Transaction, "count_many", AsyncMock(return_value=len(transactions)))
    monkeypatch.setattr(Transaction, "fetch", AsyncMock(return_value=transactions[0]))
    monkeypatch.setattr(Transaction, "save", AsyncMock())
    monkeypatch.setattr(
        Transaction, "fetch_for_category_in_range", AsyncMock(return_value=transactions[:3])
    )
    monkeypatch.setattr(Account, "fetch_all", AsyncMock(return_value=accounts))
    monkeypatch.setattr(Asset, "fetch_all", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        settings,
        "_profile",
        AsyncMock(
            return_value={
                "first": "Alex",
                "last": "Morgan",
                "email": "alex@example.com",
            }
        ),
    )

    connection = AsyncMock()
    connection.fetchrow.return_value = {"start": period.start, "end": period.end}

    async def connection_override():
        yield connection

    async def user_override():
        return "test-user"

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_connection] = connection_override
    app.dependency_overrides[auth_user] = user_override
    yield app
    app.dependency_overrides = previous_overrides
