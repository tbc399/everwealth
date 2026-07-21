from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from asyncpg import Connection
from loguru import logger

from everwealth.accounts import Account, PlaidItem
from everwealth.plaid import plaid_post
from everwealth.transactions import Transaction


def _plaid_amount_to_cents(amount: Any) -> int:
    decimal_amount = Decimal(str(amount))
    cents = (decimal_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return -int(cents)


def _transaction_description(plaid_transaction: dict) -> str:
    return (
        plaid_transaction.get("merchant_name")
        or plaid_transaction.get("name")
        or plaid_transaction.get("original_description")
        or "Plaid transaction"
    )


async def _build_transaction(
    plaid_transaction: dict, item: PlaidItem, db: Connection
) -> Transaction | None:
    account = await Account.fetch_by_plaid_account_id(item.id, plaid_transaction["account_id"], db)
    if not account:
        logger.warning(
            "Skipping Plaid transaction {} for unmapped account {} on item {}",
            plaid_transaction.get("transaction_id"),
            plaid_transaction.get("account_id"),
            item.item_id,
        )
        return None

    amount = _plaid_amount_to_cents(plaid_transaction["amount"])
    transaction_date = date.fromisoformat(plaid_transaction["date"])
    return Transaction(
        plaid_transaction_id=plaid_transaction["transaction_id"],
        user_id=item.user_id,
        account_id=account.id,
        orig_description=_transaction_description(plaid_transaction),
        description=_transaction_description(plaid_transaction),
        orig_amount=amount,
        amount=amount,
        orig_date=transaction_date,
        date=transaction_date,
    )


async def sync_item_transactions(item_id: str, db: Connection) -> None:
    item = await PlaidItem.fetch_by_item_id(item_id, db)
    if not item:
        logger.warning("Received Plaid transaction sync for unknown item {}", item_id)
        return

    cursor = item.transactions_cursor
    next_cursor = cursor
    added_or_modified: list[Transaction] = []
    removed_ids: list[str] = []

    while True:
        payload = {"access_token": item.access_token}
        if next_cursor:
            payload["cursor"] = next_cursor
        response = await plaid_post("/transactions/sync", payload)

        for plaid_transaction in response.get("added", []):
            transaction = await _build_transaction(plaid_transaction, item, db)
            if transaction:
                added_or_modified.append(transaction)

        for plaid_transaction in response.get("modified", []):
            transaction = await _build_transaction(plaid_transaction, item, db)
            if transaction:
                added_or_modified.append(transaction)

        removed_ids.extend(
            plaid_transaction["transaction_id"]
            for plaid_transaction in response.get("removed", [])
            if plaid_transaction.get("transaction_id")
        )

        next_cursor = response.get("next_cursor")
        if not response.get("has_more", False):
            break

    async with db.transaction():
        await Transaction.upsert_plaid_many(added_or_modified, db)
        await Transaction.delete_plaid_transactions(item.user_id, removed_ids, db)
        await item.save_transactions_cursor(next_cursor, db)
        await db.execute(
            """
            UPDATE accounts
            SET last_sync = $1, updated_at = $1
            WHERE plaid_item_id = $2
            """,
            datetime.utcnow(),
            item.id,
        )

    logger.info(
        "Synced Plaid transactions for item {}: {} upserted, {} removed",
        item.item_id,
        len(added_or_modified),
        len(removed_ids),
    )
