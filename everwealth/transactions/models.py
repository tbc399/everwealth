from datetime import date
from typing import Iterable, List, Optional

from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, Field, PositiveFloat
from shortuuid import uuid

from everwealth.auth import User
from everwealth.budgets import Category


class TransactionRule(BaseModel):
    pass


class Transaction(BaseModel):
    """
    TODO: should I add an original set of fields?
    """

    id: str = Field(default_factory=uuid, min_length=22, max_length=22)
    source_hash: Optional[int] = Field(default=None)
    user_id: str  # FK to the user
    user: Optional[User] = None
    account_id: Optional[str] = None  # FK to the account
    description: str = Field(max_length=128)
    amount: float
    category_id: Optional[str] = None  # FK to Category
    category_name: Optional[str] = None
    date: date  # unix epoch time in ns
    notes: Optional[str] = Field(max_length=256, default=None)
    # tags: Optional[List[Tag]] = None
    hidden: Optional[bool] = False

    def hash(self):
        if not self.source_hash:
            # we don't want to override the original hash in case the constituent fields have changed
            self.source_hash = hash(f"{self.date}{self.description}{self.amount}")

    async def create(self, conn: Connection):
        transaction = Transaction()
        transaction.hash()
        return transaction

    async def update(self, db: Connection):
        dump = self.model_dump(exclude=("user", "category_name", "account"))
        columns = ",".join(dump.keys())
        values = dump.values()
        print(values)
        place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
        sql = f"UPDATE transactions SET ({columns}) = ({place_holders}) WHERE id = '{self.id}'"
        logger.debug(f"Executing sql {sql}")
        async with db.transaction():
            await db.execute(sql, *values)

    @staticmethod
    async def create_many(transactions, db: Connection):
        if not len(transactions):
            return
        # pull the first element to get the
        dump = transactions[0].model_dump(exclude=("user", "category_name", "account"))
        columns = ",".join(dump.keys())
        values = dump.values()
        place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
        sql = f"INSERT INTO transactions ({columns}) VALUES ({place_holders})"
        logger.debug(f"Executing sql {sql}")
        async with db.transaction():
            await db.executemany(
                sql,
                (
                    list(x.model_dump(exclude=("user", "category_name", "account")).values())
                    for x in transactions
                ),
            )

    @staticmethod
    async def fetch(id: str, db: Connection):
        sql = f"SELECT transactions.*, categories.name AS category_name FROM transactions LEFT JOIN categories ON category_id = categories.id WHERE transactions.id = '{id}'"
        logger.debug(f"Executing sql {sql}")
        transaction = await db.fetchrow(sql)
        return Transaction.model_validate(dict(transaction))

    @staticmethod
    async def fetch_many(user_id: str, db: Connection):
        sql = f"SELECT transactions.*, categories.name as category_name FROM transactions LEFT JOIN categories ON category_id = categories.id WHERE transactions.user_id = '{user_id}'"
        logger.debug(f"Executing sql {sql}")
        transactions = await db.fetch(sql)
        return [Transaction.model_validate(dict(x)) for x in transactions]

    @staticmethod
    async def fetch_many_by_month(user_id: str, year: int, month: int, db: Connection):
        # TODO: need to figure out how to index

        sql = f"SELECT * FROM transactions WHERE user_id = '{user_id}' AND date BETWEEN  AND "
        transactions = await db.fetch(sql)
        return [Transaction.model_validate_json(x["data"]) for x in transactions]
