from datetime import datetime
from pydantic import Field
from shortuuid import uuid
from typing import Optional, List

from asyncpg import Connection
from pydantic import BaseModel, EmailStr


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
