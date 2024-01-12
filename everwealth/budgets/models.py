from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, EmailStr


class Budget(BaseModel):
    id: uuid
    month: datetime
    name: str
    total: float
    rollover: bool

    async def save(self):
        # write to db
        # determine if create or update with the ID
        pass

    async def duplicate(self):
        # duplicate from one month to the next
        pass
