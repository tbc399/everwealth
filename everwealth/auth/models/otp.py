from pydantic import Field, EmailStr, PositiveInt, BaseModel
from shortuuid import uuid
from datetime import datetime, timedelta
import random


class OneTimePass(BaseModel):
    id: str = Field(default_factory=uuid)
    code: PositiveInt = Field(max_digits=4, default_factory=lambda: random.randint(1000,9999))
    email: EmailStr
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    

async def create(email: str):
    return


async def fetch(id: str):
    return

