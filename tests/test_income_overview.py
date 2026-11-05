import sqlite3
from unittest.mock import AsyncMock

import pytest

from everwealth.budgets import BudgetOverview, BudgetPeriod


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_amount, expected", [(None, 1200), (5000, 5000), (0, 0)])
async def test_parent_income_plan_overrides_subcategory_plans(parent_amount, expected):
    with sqlite3.connect(":memory:") as sql:
        sql.row_factory = sqlite3.Row
        sql.executescript("""
            CREATE TABLE categories (id TEXT, name TEXT, type TEXT, parent_id TEXT);
            CREATE TABLE budgets (user_id TEXT, period_id TEXT, category_id TEXT, amount INTEGER);
            INSERT INTO categories VALUES ('income', 'Income', 'income', NULL),
                ('salary', 'Salary', 'income', 'income'), ('food', 'Food', 'expense', NULL);
            INSERT INTO budgets VALUES ('user', 'period', 'salary', 1200),
                ('user', 'period', 'food', 300), ('other-user', 'period', 'income', 9000),
                ('user', 'other-period', 'income', 8000);
        """)
        if parent_amount is not None:
            sql.execute("INSERT INTO budgets VALUES ('user', 'period', 'income', ?)", (parent_amount,))

        async def fetchrow(query, *args):
            if "AS current_income" in query:
                return {"current_income": 0, "current_spend": 0}
            return dict(sql.execute(query, {str(i): value for i, value in enumerate(args, 1)}).fetchone())

        db = AsyncMock()
        db.fetchrow.side_effect = fetchrow
        period = BudgetPeriod.for_month("user", 2026, 11)
        period.id = "period"
        overview = await BudgetOverview.fetch("user", period, db)
    assert overview.expected_income == expected
    assert overview.expected_spend == 300
