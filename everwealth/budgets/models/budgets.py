from calendar import monthrange
from datetime import date, datetime, time
from typing import Optional

from asyncpg import Connection
from pydantic import BaseModel, Field
from shortuuid import uuid


class BudgetPeriod(BaseModel):
    id: str = Field(default_factory=uuid)
    user_id: str
    start: datetime
    end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def for_month(cls, user_id: str, year: int, month: int) -> "BudgetPeriod":
        last_day = monthrange(year, month)[1]
        return cls(
            user_id=user_id,
            start=datetime.combine(date(year, month, 1), time.min),
            end=datetime.combine(date(year, month, last_day), time.max),
        )

    async def save(self, db: Connection) -> "BudgetPeriod":
        await db.execute(
            """
            INSERT INTO budget_periods (id, user_id, start, "end", created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO NOTHING
            """,
            self.id,
            self.user_id,
            self.start,
            self.end,
            self.created_at,
        )
        return self

    @staticmethod
    async def fetch_for_month(
        user_id: str, year: int, month: int, db: Connection
    ) -> Optional["BudgetPeriod"]:
        record = await db.fetchrow(
            """
            SELECT * FROM budget_periods
            WHERE user_id = $1
              AND EXTRACT(YEAR FROM start) = $2
              AND EXTRACT(MONTH FROM start) = $3
            ORDER BY start DESC LIMIT 1
            """,
            user_id,
            year,
            month,
        )
        return BudgetPeriod.model_validate(dict(record)) if record else None

    @staticmethod
    async def current(user_id: str, db: Connection) -> "BudgetPeriod":
        now = datetime.utcnow()
        period = await BudgetPeriod.fetch_for_month(user_id, now.year, now.month, db)
        if period:
            return period
        return await BudgetPeriod.for_month(user_id, now.year, now.month).save(db)


class BudgetView(BaseModel):
    id: str
    user_id: str
    category_id: str
    category_name: str
    amount: int
    rollover: bool = False
    transactions_total: float = 0

    @staticmethod
    async def fetch_all_by_month(
        user_id: str, year: int, month: int, db: Connection
    ) -> list["BudgetView"]:
        records = await db.fetch(
            """
            SELECT b.id, b.user_id, b.category_id, c.name AS category_name,
                   b.amount, COALESCE(b.rollover, FALSE) AS rollover,
                   COALESCE(SUM(t.amount), 0) / 100.0 AS transactions_total
            FROM budgets b
            JOIN budget_periods p ON p.id = b.period_id
            JOIN categories c ON c.id = b.category_id
            LEFT JOIN transactions t
              ON t.category_id = b.category_id
             AND t.user_id = b.user_id
             AND t.date BETWEEN p.start::date AND p."end"::date
             AND COALESCE(t.hidden, FALSE) = FALSE
            WHERE b.user_id = $1
              AND EXTRACT(YEAR FROM p.start) = $2
              AND EXTRACT(MONTH FROM p.start) = $3
            GROUP BY b.id, c.name
            ORDER BY c.name
            """,
            user_id,
            year,
            month,
        )
        return [BudgetView.model_validate(dict(record)) for record in records]

    @staticmethod
    async def fetch(budget_id: str, user_id: str, db: Connection) -> Optional["BudgetView"]:
        record = await db.fetchrow(
            """
            SELECT b.id, b.user_id, b.category_id, c.name AS category_name,
                   b.amount, COALESCE(b.rollover, FALSE) AS rollover,
                   COALESCE(SUM(t.amount), 0) / 100.0 AS transactions_total
            FROM budgets b
            JOIN budget_periods p ON p.id = b.period_id
            JOIN categories c ON c.id = b.category_id
            LEFT JOIN transactions t
              ON t.category_id = b.category_id
             AND t.user_id = b.user_id
             AND t.date BETWEEN p.start::date AND p."end"::date
            WHERE b.id = $1 AND b.user_id = $2
            GROUP BY b.id, c.name
            """,
            budget_id,
            user_id,
        )
        return BudgetView.model_validate(dict(record)) if record else None


class Budget(BaseModel):
    id: str = Field(default_factory=uuid)
    period_id: str
    user_id: str
    category_id: str
    amount: int
    rollover: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def fetch(budget_id: str, user_id: str, db: Connection) -> Optional["Budget"]:
        record = await db.fetchrow(
            "SELECT * FROM budgets WHERE id = $1 AND user_id = $2", budget_id, user_id
        )
        return Budget.model_validate(dict(record)) if record else None

    async def save(self, db: Connection) -> None:
        await db.execute(
            """
            INSERT INTO budgets (
                id, period_id, user_id, category_id, amount, rollover, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (id) DO UPDATE SET
                amount = EXCLUDED.amount,
                rollover = EXCLUDED.rollover,
                updated_at = EXCLUDED.updated_at
            """,
            self.id,
            self.period_id,
            self.user_id,
            self.category_id,
            self.amount,
            self.rollover,
            self.created_at,
            datetime.utcnow(),
        )


class BudgetOverview(BaseModel):
    expected_income: float = 0
    current_income: float = 0
    expected_spend: float = 0
    current_spend: float = 0

    @staticmethod
    async def fetch(user_id: str, period: BudgetPeriod, db: Connection) -> "BudgetOverview":
        row = await db.fetchrow(
            """
            SELECT
              COALESCE(SUM(CASE WHEN c.type = 'income' THEN ABS(t.amount) ELSE 0 END), 0) / 100.0 AS current_income,
              COALESCE(SUM(CASE WHEN c.type = 'expense' OR t.category_id IS NULL THEN ABS(t.amount) ELSE 0 END), 0) / 100.0 AS current_spend
            FROM transactions t
            LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.user_id = $1
              AND t.date BETWEEN $2::date AND $3::date
              AND COALESCE(t.hidden, FALSE) = FALSE
            """,
            user_id,
            period.start,
            period.end,
        )
        expected = await db.fetchrow(
            """
            SELECT
              COALESCE(SUM(CASE WHEN c.type = 'income' THEN b.amount ELSE 0 END), 0) AS expected_income,
              COALESCE(SUM(CASE WHEN c.type = 'expense' THEN b.amount ELSE 0 END), 0) AS expected_spend
            FROM budgets b
            JOIN categories c ON c.id = b.category_id
            WHERE b.user_id = $1 AND b.period_id = $2
            """,
            user_id,
            period.id,
        )
        return BudgetOverview(**dict(row), **dict(expected))
