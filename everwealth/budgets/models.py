from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import asyncpg
from pydantic import BaseModel
from shortuuid import ShortUUID


class Budget(BaseModel):
    id: str = ShortUUID()  # shortuuid
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    category: str  # to link to Category
    total: float = 0.0
    rollover: Optional[bool] = False
    account: str = ""  # shortuuid

    async def save(self):
        # write to db
        # determine if create or update with the ID
        return

    async def duplicate(self):
        # duplicate from one month to the next
        return


async def get_current_budgets(account: str) -> List[Budget]:
    return


async def create_new_budget(account: str) -> None:
    # valdiate category
    #
    budget = Budget()
    return
