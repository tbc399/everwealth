from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, PositiveInt
from shortuuid import ShortUUID, uuid
from asyncpg import Connection
from enum import Enum
from everwealth.settings.categories import Category
from everwealth.auth import User

from loguru import logger


class Frequency(Enum):
    yearly = "yearly"
    monthly = "monthly"


class BudgetCategoryView(BaseModel):
    id: str
    name: str


class Budget(BaseModel):
    id: str = Field(default_factory=uuid)  # shortuuid
    user_id: str = None
    user: User
    category_id: str = None  # to link to Category
    category: Category
    amount: int = None
    rollover: Optional[bool] = False
    frequency: Frequency = Field(default=Frequency.monthly)
    year: PositiveInt = Field(default_factory=lambda: datetime.utcnow().year)
    month: Optional[PositiveInt] = Field(
        ge=1, le=12, default_factory=lambda: datetime.utcnow().month
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


async def fetch_all_by_month(user_id: str, year: int, month: int, db: Connection) -> List[Budget]:
    logger.debug(f"Fetching budgets for {user_id}")
    # TODO: filter on user id
    # records = await db.fetch(
    #    f'SELECT data from budgets where data @> \'{{"user_id": "{user_id}"}}\''
    # )
    # TODO need to filter for current month
    records = await db.fetch(
        f"SELECT * FROM budgets WHERE user_id = '{user_id}' AND year = {year} AND month = {month}"
    )
    return [Budget.model_validate_json(x) for x in records]


async def fetch(id: str, user_id: str, db: Connection) -> Budget:
    logger.debug(f"Fetching budget for id {id} and user_id {user_id}")
    # record = await db.fetchrow(
    #    f'SELECT data from budgets where data @> \'{{"user_id": "{user_id}", "id": "{id}"}}\''
    # )
    record = await db.fetchrow(f"SELECT * FROM budgets WHERE user_id = '{user_id}' AND id = '{id}'")
    return Budget.model_validate_json(record)


async def create(budget: Budget, db: Connection) -> Budget:
    # validate that category is not already being used for a budget
    # await db.execute(f"INSERT INTO budgets (data) VALUES ('{budget.model_dump_json()}')")
    dump = budget.model_dump(exclude=("user", "category"))
    column_names = ",".join(dump.keys())
    value_names = ",".join(dump.values())
    with db.transaction():
        await db.execute(f"INSERT INTO budgets ({column_names}) VALUES ({value_names})")
    return budget
