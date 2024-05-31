from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from shortuuid import ShortUUID


class Budget(BaseModel):
    id: str = ShortUUID()  # shortuuid
    user_id: str = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    category: str = None  # to link to Category
    amount: int = None
    rollover: Optional[bool] = False


async def get_current_budgets(account: str) -> List[Budget]:
    return


async def create_new_budget(account: str) -> None:
    # valdiate category
    #
    budget = Budget()
    return
