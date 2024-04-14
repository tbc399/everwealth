from pydantic import Field, BaseModel, PositiveFloat
from everwealth.settings import Category
from shortuuid import uuid
from typing import Optional, List, Iterable
from datetime import datetime
from everwealth.users import User
from asyncpg import Connection


class Account(BaseModel):
    """A third party account to pull transaction info from"""

    user: User


class AccountTransaction(BaseModel):
    id: str = Field(default_factory=uuid)
    source_hash: int = 0  # used to match transactions to source
    account: Account
    description: str = Field(max_length=128)
    amount: float
    category: Optional[Category] = None
    date: datetime
    notes: Optional[str] = Field(max_length=128, default=None)
    # tags: Optional[List[Tag]] = None
    hidden: Optional[bool] = False

    def hash(self):
        if not self.source_hash:
            self.source_hash = hash("".join((self.date, self.description, self.amount)))


async def create(account: Account, description: str, amount, conn: Connection, category=None):
    transaction = AccountTransaction()
    transaction.hash()

    return transaction


async def bulk_create(transactions: Iterable[AccountTransaction], conn: Connection):
    async with conn.transaction():
        await conn.executemany(
            "INSERT INTO transactions (data) VALUES ($1)",
            ((x.model_dump_json(),) for x in transactions),
        )


async def fetch(id: str, user: User, conn: Connection):
    transaction = await conn.fetchrow(
        f'SELECT data from transactions where data @> \'{{"id": "{id}"}}\''
    )
    return AccountTransaction.model_validate_json(transaction)


async def fetch_many(user: User, conn: Connection):
    # TODO: need to figure out how to index
    transactions = await conn.fetch(
        f'SELECT data from transactions where data[\'account\'][\'user\'][\'email\'] = \'"{user.email}"\''
    )
    return [AccountTransaction.model_validate_json(x["data"]) for x in transactions]
