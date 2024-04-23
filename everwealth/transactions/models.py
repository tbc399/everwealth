from pydantic import Field, BaseModel, PositiveFloat
from everwealth.settings import Category
from shortuuid import uuid
from typing import Optional, List, Iterable
from datetime import date
from everwealth.users import User
from asyncpg import Connection


class Account(BaseModel):
    """A third party account to pull transaction info from"""

    user: str


class TransactionRule(BaseModel):
    pass


class AccountTransaction(BaseModel):
    id: str = Field(default_factory=uuid)
    user: str  # the short uuid of the owning user
    source_hash: int = 0  # used to match transactions to source
    account: Account
    description: str = Field(max_length=128)
    amount: float
    # category: Optional[Category] = Field(default_factory=lambda: Category(name="Uncategorized", user=None))
    category: Optional[str] = None # the short uuid of the category
    date: date
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

async def update(transaction: AccountTransaction, conn: Connection):
    async with conn.transaction():
        # TODO: learn how to replace with proper prepared statements
        await conn.execute(
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
        f'SELECT data from transactions where data[\'id\'] = \'"{id}"\''
    )
    return AccountTransaction.model_validate_json(transaction["data"])


async def fetch_many(user_id: str, conn: Connection):
    # TODO: need to figure out how to index
    #transactions = await conn.fetch(
    #    f'SELECT data from transactions where data[\'account\'][\'user\'] = \'"{user_id}"\''
    #)
    transactions = await conn.fetch(
        'SELECT data from transactions'
    )
    return [AccountTransaction.model_validate_json(x["data"]) for x in transactions]
