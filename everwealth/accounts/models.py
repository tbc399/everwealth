from datetime import datetime

from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, Field
from shortuuid import uuid


class AccountView(BaseModel):
    pass


class Account(BaseModel):
    id: str = Field(min_length=22, max_length=22, default_factory=uuid)
    name: str
    user_id: str = Field(min_length=22, max_length=22, default_factory=uuid)
    institution_name: str
    stripe_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def fetch_all(user_id: str, db: Connection):
        logger.debug(f"Fetching budget for id {id} and user_id {user_id}")
        record = await db.fetch(f"SELECT * FROM accounts WHERE user_id = '{user_id}'")
        return Account.model_validate(dict(record))


'''
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
'''
