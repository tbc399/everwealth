from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Optional

from pydantic import BaseModel, Field, PositiveInt, ConfigDict
from shortuuid import uuid
from asyncpg import Connection
from enum import Enum
from everwealth.auth import User
from .categories import Category

from loguru import logger


class Frequency(Enum):
    yearly = "yearly"
    monthly = "monthly"

class BudgetMonth(Enum):
    JAN = "Jan"
    FEB = "Feb"
    MAR = "Mar"
    APR = "Apr"
    MAY = "May"
    JUN = "Jun"
    JUL = "Jul"
    AUG = "Aug"
    SEPT = "Sept"
    OCT = "Oct"
    NOV = "Nov"
    DEC = "Dec"

class BudgetMonthsView(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    month: BudgetMonth
    on_budget: Optional[bool] = None
    current: bool = False

    @staticmethod
    async def fetch_by_year(user_id: str, year: int, db: Connection):
        sql = f"""
            SELECT * FROM budgets WHERE
        """
        #records = await db.fetch(sql)
        months = [BudgetMonthsView(month=month) for month in BudgetMonth]
        return months

class BudgetView(BaseModel):
    """A read only model for budgets"""

    id: str
    user_id: str
    category_id: str
    category_name: str
    amount: int = None
    frequency: Frequency = Field(default=Frequency.monthly)
    year: PositiveInt = Field(default_factory=lambda: datetime.utcnow().year)
    month: Optional[PositiveInt] = Field(
        ge=1, le=12, default_factory=lambda: datetime.utcnow().month
    )
    transactions_total: float

    @staticmethod
    async def fetch_all_by_month(user_id: str, year: int, month: int, db: Connection):
        start_of_month = date(year=year, month=month, day=1)
        end_of_month = start_of_month + relativedelta(months=+1, days=-1, day=1)
        sql = f"""
        SELECT budgets.*,
            categories.name as category_name, SUM(COALESCE(transactions.amount, 0)) as transactions_total
            FROM budgets LEFT JOIN categories ON budgets.category_id = categories.id
            LEFT JOIN transactions ON budgets.category_id = transactions.category_id
            WHERE budgets.user_id = '{user_id}' 
                AND year = {year} 
                AND month = {month} 
                AND (transactions.date BETWEEN '{start_of_month}' AND '{end_of_month}' OR transactions.date is NULL) 
                GROUP BY budgets.id, categories.id
        """
        logger.debug(f"Executing sql {sql}")
        records = await db.fetch(sql)
        return [BudgetView.model_validate(dict(record)) for record in records]


class Budget(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=uuid)  # shortuuid
    user_id: str = None
    user: Optional[User] = None
    category_id: str = None
    category: Optional[Category] = None
    amount: int = None
    rollover: Optional[bool] = False
    frequency: Frequency = Field(default=Frequency.monthly)
    year: PositiveInt = Field(default_factory=lambda: datetime.utcnow().year)
    month: Optional[PositiveInt] = Field(
        ge=1, le=12, default_factory=lambda: datetime.utcnow().month
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def fetch(id: str, user_id: str, db: Connection):
        logger.debug(f"Fetching budget for id {id} and user_id {user_id}")
        # record = await db.fetchrow(
        #    f'SELECT data from budgets where data @> \'{{"user_id": "{user_id}", "id": "{id}"}}\''
        # )
        record = await db.fetchrow(
            f"SELECT * FROM budgets WHERE user_id = '{user_id}' AND id = '{id}'"
        )
        return Budget.model_validate(dict(record))

	
    async def create(self, db: Connection):
        # TODO validate that category is not already being used for a budget
        dump = self.model_dump(
            exclude=("user", "category"),
        )
        print(dump)
        columns = ",".join(dump.keys())
        values = dump.values()
        place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
        sql = f"INSERT INTO budgets ({columns}) VALUES ({place_holders})"
        logger.debug(f"Executing sql {sql}")
        async with db.transaction():
            await db.execute(sql, *values)
