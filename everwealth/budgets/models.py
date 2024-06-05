from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from shortuuid import ShortUUID, uuid
from asyncpg import Connection
from enum import Enum

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    category: Optional[BudgetCategoryView] = None  # to link to Category
    amount: int = None
    rollover: Optional[bool] = False
    frequency: Frequency = Field(default=Frequency.monthly)


async def fetch(account: str) -> List[Budget]:
    return

async def fetch_many(user_id: str, db: Connection) -> List[Budget]:
    logger.debug(f"Fetching budgets for {user_id}")
    # TODO: filter on user id
    records = await db.fetch(
        f'SELECT data from budgets where data @> \'{{"user_id": "{user_id}"}}\''
    )
    return [Budget.model_validate_json(x["data"]) for x in records]


async def create(user_id: str, db: Connection) -> Budget:
    budgets = await fetch_many(user_id, db)
    if name not in budgets:
        category = Category(name=name, user_id=user_id)
    budget = Budget(user_id=user_id, category=None)
    await db.execute(f"INSERT INTO categories (data) VALUES ('{category.model_dump_json()}')")
    return category
