from datetime import datetime
from typing import Optional, List

from asyncpg import Connection
from pydantic import BaseModel, EmailStr


class ConnectedAccount(BaseModel):
    """A third party account to pull transaction info from"""

    pass


class AccountTransaction(BaseModel):
    id: str
    hash: str  # used to match transactions coming from source
    account: Optional[ConnectedAccount] = None
    description: str
    amount: float
    category: str  # fk to Category
    date: datetime
    notes: str
    hidden: Optional[bool] = False


class Budget(BaseModel):
    category: str  # linked to categories
    amount: int
    spent: int

    # rollover any unused amount at the end of each month
    rollover: bool

    def aggregate_transactions():
        """Compute total current spend for this budget"""
        return

    @property
    def percentage(self):
        return round((self.spent / self.amount) * 100)


class TransactionRule(BaseModel):
    """setup a rule to convert a transaction

    This can only be done on automatic transactions or csv uploaded transactions
    """

    by_description: bool
    description_contains: str
    by_amount: bool
    pass


transaction_rules: List[TransactionRule] = None
