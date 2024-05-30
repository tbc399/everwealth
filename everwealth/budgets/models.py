from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import asyncpg
from pydantic import BaseModel, Field
from shortuuid import ShortUUID


class Budget(BaseModel):
    id: str = ShortUUID()  # shortuuid
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    category: str  # to link to Category
    total: float
    rollover: Optional[bool] = False


async def get_current_budgets(account: str) -> List[Budget]:
    return


async def create_new_budget(account: str) -> None:
    # valdiate category
    #
    budget = Budget()
    return
