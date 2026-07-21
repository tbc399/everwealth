from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from asyncpg import Connection
from pydantic import BaseModel, ConfigDict, Field
from shortuuid import uuid


class AssetType(str, Enum):
    vehicle = "vehicle"
    property = "property"
    other = "other"


class Asset(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=uuid)
    name: str
    type: AssetType
    user_id: str
    last_sync: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def fetch_all(user_id: str, db: Connection) -> list["Asset"]:
        records = await db.fetch(
            "SELECT * FROM assets WHERE user_id = $1 ORDER BY created_at DESC", user_id
        )
        return [Asset.model_validate(dict(record)) for record in records]


class AccountType(str, Enum):
    cash = "cash"
    credit = "credit"
    investment = "investment"
    other = "other"
    manual = "manual"


class AccountSubType(str, Enum):
    checking = "checking"
    savings = "savings"
    credit_card = "credit_card"
    line_of_credit = "line_of_credit"
    mortgage = "mortgage"
    other = "other"


class PlaidItem(BaseModel):
    id: str = Field(default_factory=uuid)
    user_id: str
    access_token: str
    institution_id: Optional[str] = None
    item_id: str
    transactions_cursor: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def save(self, db: Connection) -> None:
        item_id = await db.fetchval(
            """
            INSERT INTO plaid_items
                (
                    id, user_id, access_token, institution_id, item_id,
                    transactions_cursor, created_at, updated_at
                )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (item_id) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                institution_id = EXCLUDED.institution_id,
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """,
            self.id,
            self.user_id,
            self.access_token,
            self.institution_id,
            self.item_id,
            self.transactions_cursor,
            self.created_at,
            self.updated_at,
        )
        self.id = item_id

    async def save_transactions_cursor(self, cursor: Optional[str], db: Connection) -> None:
        self.transactions_cursor = cursor
        await db.execute(
            """
            UPDATE plaid_items
            SET transactions_cursor = $1, updated_at = $2
            WHERE id = $3
            """,
            cursor,
            datetime.utcnow(),
            self.id,
        )

    @staticmethod
    async def fetch_by_item_id(item_id: str, db: Connection) -> Optional["PlaidItem"]:
        record = await db.fetchrow("SELECT * FROM plaid_items WHERE item_id = $1", item_id)
        return PlaidItem.model_validate(dict(record)) if record else None


class Account(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=uuid)
    name: str
    type: AccountType
    sub_type: AccountSubType = AccountSubType.other
    user_id: str
    institution_name: str = ""
    last4: str = ""
    stripe_id: Optional[str] = None
    plaid_item_id: Optional[str] = None
    plaid_account_id: Optional[str] = None
    last_sync: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def last_sync_display(self) -> str:
        if not self.last_sync:
            return "never"
        elapsed = datetime.utcnow() - self.last_sync
        if elapsed < timedelta(minutes=5):
            return "a moment ago"
        if elapsed < timedelta(hours=24):
            return "today"
        if elapsed < timedelta(days=7):
            return "this week"
        return "over a week ago"

    @staticmethod
    async def fetch_all(user_id: str, db: Connection) -> list["Account"]:
        records = await db.fetch(
            "SELECT * FROM accounts WHERE user_id = $1 ORDER BY type, created_at", user_id
        )
        return [Account.model_validate(dict(record)) for record in records]

    @staticmethod
    async def fetch_by_plaid_account_id(
        plaid_item_id: str, plaid_account_id: str, db: Connection
    ) -> Optional["Account"]:
        record = await db.fetchrow(
            """
            SELECT * FROM accounts
            WHERE plaid_item_id = $1 AND plaid_account_id = $2
            """,
            plaid_item_id,
            plaid_account_id,
        )
        return Account.model_validate(dict(record)) if record else None

    async def save(self, db: Connection) -> None:
        await db.execute(
            """
            INSERT INTO accounts (
                id, name, type, sub_type, user_id, institution_name, last4,
                plaid_item_id, plaid_account_id, last_sync, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                sub_type = EXCLUDED.sub_type,
                institution_name = EXCLUDED.institution_name,
                last4 = EXCLUDED.last4,
                plaid_item_id = EXCLUDED.plaid_item_id,
                plaid_account_id = EXCLUDED.plaid_account_id,
                last_sync = EXCLUDED.last_sync,
                updated_at = EXCLUDED.updated_at
            """,
            self.id,
            self.name,
            self.type,
            self.sub_type,
            self.user_id,
            self.institution_name,
            self.last4,
            self.plaid_item_id,
            self.plaid_account_id,
            self.last_sync,
            self.created_at,
            self.updated_at,
        )
