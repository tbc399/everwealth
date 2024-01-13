from dataclasses import dataclass
from datetime import datetime
from typing import List

import asyncpg
from pydantic import BaseModel
from shortuuid import ShortUUID


class Budget(BaseModel):
    id: str  # shortuuid
    created_at: datetime
    updated_at: datetime
    category: str  # to link to Category
    total: float
    rollover: bool
    account: str  # shortuuid

    async def save(self):
        # write to db
        # determine if create or update with the ID
        return

    async def duplicate(self):
        # duplicate from one month to the next
        return


async def get_current_budgets(account: str) -> List[Budget]:
    return 3
