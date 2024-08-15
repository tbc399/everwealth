from datetime import datetime
from enum import Enum
from typing import List, Optional

from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, Field
from shortuuid import uuid


class AccountView(BaseModel):
    pass


class AssetType(Enum):
    vehicle = "vehicle"
    property = "property"
    other = "other"


class Asset:
    id: str = Field(min_length=22, max_length=22, default_factory=uuid)
    name: str
    type: AssetType
    user_id: str = Field(min_length=22, max_length=22, default_factory=uuid)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AccountType(Enum):
    cash = "cash"
    credit = "credit"
    investment = "investment"
    other = "other"
    manual = "manual"


class Account(BaseModel):
    id: str = Field(min_length=22, max_length=22, default_factory=uuid)
    name: str
    type: AccountType
    user_id: str = Field(min_length=22, max_length=22, default_factory=uuid)
    institution_name: str
    stripe_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def fetch_by_type(user_id: str, type: str, db: Connection) -> List["Account"]:
        sql = f"SELECT * FROM accounts WHERE user_id = '{user_id}' and type = '{type}'"
        logger.debug(f"Executing sql {sql}")
        records = await db.fetch(sql)
        if not records:
            return []
        return [Account.model_validate(dict(record)) for record in records]

    @staticmethod
    async def fetch_by_stripe_id(stripe_id: str, db: Connection) -> "Account":
        sql = f"SELECT * FROM accounts WHERE stripe_id = '{stripe_id}'"
        logger.debug(f"Executing sql {sql}")
        record = await db.fetchrow(sql)
        if not record:
            return None
        return Account.model_validate(dict(record))

    async def save(self, db: Connection):
        dump = self.model_dump()
        columns = ",".join(dump.keys())
        values = dump.values()
        place_holders = ",".join((f"${x}" for x in range(1, len(values) + 1)))
        sql = f"INSERT INTO accounts ({columns}) VALUES ({place_holders})"
        logger.debug(f"Executing sql {sql}")
        async with db.transaction():
            await db.execute(sql, *values)


"""
stripe_account = {
    "id": "fca_1MwVK82eZvKYlo2Cjw8FMxXf",
    "object": "linked_account",
    "account_holder": {"customer": "cus_9s6XI9OFIdpjIg", "type": "customer"},
    "balance": null,
    "balance_refresh": null,
    "category": "cash",
    "created": 1681412208,
    "display_name": "Sample Checking Account",
    "institution_name": "StripeBank",
    "last4": "6789",
    "livemode": false,
    "ownership": null,
    "ownership_refresh": null,
    "permissions": [],
    "status": "active",
    "subcategory": "checking",
    "subscriptions": [],
    "supported_payment_method_types": ["us_bank_account"],
    "transaction_refresh": null,
}
"""
