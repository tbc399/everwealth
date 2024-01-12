from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, EmailStr


class Budget(BaseModel):
    month: datetime
    name: str
    total: float
    rollover: bool

    async def create(name: str, )


class ConnectedAccount(BaseModel):
    """A third party account to pull transaction info from"""

    pass


class AccountTransaction(BaseModel):
    account: ConnectedAccount
    description: str
    amount: float
    date: datetime
    notes: str


class User(BaseModel):
    first: str
    last: str
    email: EmailStr  # TODO: is this necessary?


class Account(BaseModel):
    user: User
