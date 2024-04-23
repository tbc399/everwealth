from pydantic import Field, IPvAnyAddress, BaseModel, PositiveInt, EmailStr
from datetime import datetime, timedelta
from shortuuid import uuid


class Session(BaseModel):
    id: str = Field(default_factory=uuid)  # a short uuid
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=1))
    user_id: str
    ip_address: IPvAnyAddress


async def create(user: str):
    return


async def fetch(id: str):
    return


