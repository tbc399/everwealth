from datetime import date, datetime
from typing import Optional

from asyncpg import Connection
from pydantic import BaseModel, Field
from shortuuid import uuid


class TransactionRefresh(BaseModel):
    id: Optional[str] = None
    user_id: str
    account_id: str
    stripe_id: Optional[str] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionRule(BaseModel):
    id: str

    @staticmethod
    async def fetch_many(user_id: str, db: Connection) -> list["TransactionRule"]:
        return []


class Transaction(BaseModel):
    id: str = Field(default_factory=uuid)
    source_hash: Optional[int] = None
    plaid_transaction_id: Optional[str] = None
    user_id: str
    account_id: Optional[str] = None
    orig_description: Optional[str] = None
    description: str
    orig_amount: Optional[int] = None
    amount: int
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    orig_date: Optional[date] = None
    date: date
    notes: Optional[str] = None
    hidden: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def display_amount(self) -> str:
        return f"{self.amount / 100:,.2f}"

    def prepare_originals(self) -> None:
        self.orig_description = self.orig_description or self.description
        self.orig_amount = self.orig_amount if self.orig_amount is not None else self.amount
        self.orig_date = self.orig_date or self.date
        self.source_hash = self.source_hash or hash(
            (self.user_id, self.account_id, self.orig_date, self.orig_description, self.orig_amount)
        )

    async def save(self, db: Connection) -> None:
        self.prepare_originals()
        await db.execute(
            """
            INSERT INTO transactions (
                id, source_hash, plaid_transaction_id, user_id, account_id,
                orig_description, description,
                orig_amount, amount, category_id, orig_date, date, notes, hidden,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            )
            ON CONFLICT (id) DO UPDATE SET
                description = EXCLUDED.description,
                amount = EXCLUDED.amount,
                category_id = EXCLUDED.category_id,
                date = EXCLUDED.date,
                notes = EXCLUDED.notes,
                hidden = EXCLUDED.hidden,
                updated_at = EXCLUDED.updated_at
            """,
            self.id,
            self.source_hash,
            self.plaid_transaction_id,
            self.user_id,
            self.account_id,
            self.orig_description,
            self.description,
            self.orig_amount,
            self.amount,
            self.category_id,
            self.orig_date,
            self.date,
            self.notes,
            self.hidden,
            self.created_at,
            datetime.utcnow(),
        )

    @staticmethod
    async def create_many(transactions: list["Transaction"], db: Connection) -> None:
        async with db.transaction():
            for transaction in transactions:
                transaction.prepare_originals()
                exists = await db.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM transactions WHERE user_id = $1 AND source_hash = $2)",
                    transaction.user_id,
                    transaction.source_hash,
                )
                if not exists:
                    await transaction.save(db)

    @staticmethod
    async def upsert_plaid_many(transactions: list["Transaction"], db: Connection) -> None:
        async with db.transaction():
            for transaction in transactions:
                transaction.prepare_originals()
                await db.execute(
                    """
                    INSERT INTO transactions (
                        id, source_hash, plaid_transaction_id, user_id, account_id,
                        orig_description, description, orig_amount, amount, category_id,
                        orig_date, date, notes, hidden, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                    ON CONFLICT (plaid_transaction_id) WHERE plaid_transaction_id IS NOT NULL
                    DO UPDATE SET
                        source_hash = EXCLUDED.source_hash,
                        account_id = EXCLUDED.account_id,
                        orig_description = EXCLUDED.orig_description,
                        orig_amount = EXCLUDED.orig_amount,
                        orig_date = EXCLUDED.orig_date,
                        description = CASE
                            WHEN transactions.description = transactions.orig_description
                            THEN EXCLUDED.description
                            ELSE transactions.description
                        END,
                        amount = CASE
                            WHEN transactions.amount = transactions.orig_amount
                            THEN EXCLUDED.amount
                            ELSE transactions.amount
                        END,
                        date = CASE
                            WHEN transactions.date = transactions.orig_date
                            THEN EXCLUDED.date
                            ELSE transactions.date
                        END,
                        updated_at = EXCLUDED.updated_at
                    WHERE transactions.user_id = EXCLUDED.user_id
                    """,
                    transaction.id,
                    transaction.source_hash,
                    transaction.plaid_transaction_id,
                    transaction.user_id,
                    transaction.account_id,
                    transaction.orig_description,
                    transaction.description,
                    transaction.orig_amount,
                    transaction.amount,
                    transaction.category_id,
                    transaction.orig_date,
                    transaction.date,
                    transaction.notes,
                    transaction.hidden,
                    transaction.created_at,
                    datetime.utcnow(),
                )

    @staticmethod
    async def delete_plaid_transactions(
        user_id: str, plaid_transaction_ids: list[str], db: Connection
    ) -> None:
        if not plaid_transaction_ids:
            return
        await db.execute(
            """
            DELETE FROM transactions
            WHERE user_id = $1 AND plaid_transaction_id = ANY($2::text[])
            """,
            user_id,
            plaid_transaction_ids,
        )

    @staticmethod
    async def fetch(transaction_id: str, user_id: str, db: Connection) -> Optional["Transaction"]:
        record = await db.fetchrow(
            """
            SELECT t.*, c.name AS category_name
            FROM transactions t LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.id = $1 AND t.user_id = $2
            """,
            transaction_id,
            user_id,
        )
        return Transaction.model_validate(dict(record)) if record else None

    @staticmethod
    async def fetch_many(
        user_id: str,
        db: Connection,
        account_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list["Transaction"]:
        records = await db.fetch(
            """
            SELECT t.*, c.name AS category_name
            FROM transactions t LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.user_id = $1 AND ($2::varchar IS NULL OR t.account_id = $2)
              AND COALESCE(t.hidden, FALSE) = FALSE
            ORDER BY t.date DESC, t.created_at DESC
            LIMIT COALESCE($3::integer, 2147483647) OFFSET $4
            """,
            user_id,
            account_id,
            limit,
            offset,
        )
        return [Transaction.model_validate(dict(record)) for record in records]

    @staticmethod
    async def count_many(user_id: str, db: Connection, account_id: Optional[str] = None) -> int:
        return await db.fetchval(
            """
            SELECT COUNT(*)
            FROM transactions t
            WHERE t.user_id = $1 AND ($2::varchar IS NULL OR t.account_id = $2)
              AND COALESCE(t.hidden, FALSE) = FALSE
            """,
            user_id,
            account_id,
        )

    @staticmethod
    async def fetch_for_category_in_range(
        user_id: str, category_id: str, start: date, end: date, db: Connection
    ) -> list["Transaction"]:
        records = await db.fetch(
            """
            SELECT t.*, c.name AS category_name
            FROM transactions t LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.user_id = $1 AND t.category_id = $2 AND t.date BETWEEN $3 AND $4
            ORDER BY t.date DESC
            """,
            user_id,
            category_id,
            start,
            end,
        )
        return [Transaction.model_validate(dict(record)) for record in records]
