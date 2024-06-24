from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, PositiveInt, ConfigDict
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


async def fetch_all_by_month(user_id: str, year: int, month: int, db: Connection) -> List[Budget]:
    sql = f"""
    SELECT budgets.*, categories.name as category_name, categories.created_at as category_created_at, categories.user_id as category_user_id FROM budgets JOIN categories ON budgets.category_id = categories.id
        WHERE budgets.user_id = '{user_id}' AND year = {year} AND month = {month}
        """
    logger.debug(f"Executing sql {sql}")
    records = await db.fetch(sql)
    budgets = []
    for record in records:
        category = Category(
            id=record.get("category_id"),
            name=record.get("category_name"),
            created_at=record.get("category_created_at"),
            user_id=record.get("category_user_id"),
        )
        budget = Budget.model_validate(dict(record))
        budget.category = category
        budgets.append(budget)
    return budgets


async def fetch(id: str, user_id: str, db: Connection) -> Budget:
    logger.debug(f"Fetching budget for id {id} and user_id {user_id}")
    # record = await db.fetchrow(
    #    f'SELECT data from budgets where data @> \'{{"user_id": "{user_id}", "id": "{id}"}}\''
    # )
    record = await db.fetchrow(f"SELECT * FROM budgets WHERE user_id = '{user_id}' AND id = '{id}'")
    return Budget.model_validate(dict(record))


async def create(budget: Budget, db: Connection) -> Budget:
    # TODO validate that category is not already being used for a budget
    dump = budget.model_dump(
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
    return budget
