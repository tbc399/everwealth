from datetime import date
from typing import Iterable, List, Optional

from asyncpg import Connection
from pydantic import BaseModel, Field, PositiveFloat
from shortuuid import uuid

from everwealth.settings.categories import Category
from everwealth.auth import User
from loguru import logger


class Account(BaseModel):
    """A third party account to pull transaction info from"""

    user: str


class TransactionRule(BaseModel):
    pass


class AccountTransactionCategoryView(BaseModel):
    id: str
    name: str


class AccountView(BaseModel):
    id: str
    name: str


class AccountTransaction(BaseModel):
    """
    TODO: should I add an original set of fields?
    """

    id: str = Field(default_factory=uuid)
    source_hash: Optional[int] = Field(default=None)
    user_id: str  # FK to the user
    user: Optional[User]
    source_hash: int = 0  # used to match transactions to source
    account: Optional[AccountView] = None
    description: str = Field(max_length=128)
    amount: float
    # category: Optional[AccountTransactionCategoryView] = None
    category_id: str  # FK to Category
    category: Optional[Category] = None
    date: int  # unix epoch time in ns
    note: Optional[str] = Field(max_length=128, default=None)
    # tags: Optional[List[Tag]] = None
    hidden: Optional[bool] = False

    def hash(self):
        if not self.source_hash:
            # we don't want to override the original hash in case the constituent fields have changed
            self.source_hash = hash(f"{self.date}{self.description}{self.amount}")


async def create(account: Account, description: str, amount, conn: Connection, category=None):
    transaction = AccountTransaction()
    transaction.hash()
    return transaction


async def update(transaction: AccountTransaction, db: Connection):
    async with db.transaction():
        # TODO: learn how to replace with proper prepared statements
        await db.execute(
            f"UPDATE transactions SET data = '{transaction.model_dump_json()}' where data['id'] = '\"{transaction.id}\"'"
        )
    return transaction


async def bulk_create(transactions: Iterable[AccountTransaction], conn: Connection):
    async with conn.transaction():
        await conn.executemany(
            "INSERT INTO transactions (data) VALUES ($1)",
            ((x.model_dump_json(),) for x in transactions),
        )


async def fetch(id: str, conn: Connection):
    transaction = await conn.fetchrow(
        f"SELECT data from transactions where data['id'] = '\"{id}\"'"
    )
    return AccountTransaction.model_validate_json(transaction["data"])


async def fetch_many(user_id: str, conn: Connection):
    logger.debug(f"Fetching transactions for user {user_id}")
    # TODO: need to figure out how to index
    transactions = await conn.fetch(
        f"SELECT data from transactions where data['user_id'] = '\"{user_id}\"'"
    )
    return [AccountTransaction.model_validate_json(x["data"]) for x in transactions]


async def fetch_many_by_month(user_id: str, month: date, conn: Connection):
    # TODO: need to figure out how to index
    month.month
    month.year
    transactions = await conn.fetch(
        f"SELECT data from transactions where data['user_id'] = '\"{user_id}\"' and data['']"
    )
    return [AccountTransaction.model_validate_json(x["data"]) for x in transactions]
