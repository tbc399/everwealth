from datetime import datetime

from pydantic import BaseModel, EmailStr




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


