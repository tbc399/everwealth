import asyncio
from datetime import datetime

import stripe
from asyncpg import Connection
from loguru import logger

from everwealth.accounts import Account
from everwealth.auth import User
from everwealth.transactions import Transaction, TransactionRefresh


async def run():
    """Periodically initiate transaction refreshes with Stripe"""

    refresh_dates = ()

    # TODO: Only accounts of type cash.checking and credit.credit_card should be setup on a refresh
    # schedule

    # TODO: accounts like credit.mortgage, investment and cash.savings will be manually updated in
    # their balance once a month. Will not collect transactions as it's more expensive

    while True:
        now = datetime.utcnow()

        if now:
            pass

        Account.fetch_all
        await schedule(user, account)

        asyncio.sleep(30)


async def schedule(user: User, account: Account, db: Connection):
    stripe_account = await stripe.financial_connections.Account.refresh_account_async(
        account.stripe_id, features=["transactions"]
    )
    logger.info(f"Refresh id {stripe_account.transaction_refresh.id}")
    refresh = TransactionRefresh(
        user_id=user.id, account_id=account.id, stripe_id=stripe_account.transaction_refresh.id
    )
    await refresh.create(db)
    logger.info(f"New transaction refresh {refresh.id} created for user {user.id}")


async def refresh(stripe_id: str, stripe_account_id: str, db: Connection):
    """Fetch new transactions from Stripe"""
    transaction_refresh = await TransactionRefresh.fetch_by_stripe_id(stripe_id, db)
    stripe_transactions = await stripe.financial_connections.Transaction.list_async(
        account=stripe_account_id,
        # transaction_refresh={"after": stripe_id}
    )
    print(stripe_transactions)
    transactions = [
        Transaction(
            user_id=transaction_refresh.user_id,
            account_id=transaction_refresh.account_id,
            description=t.description,
            amount=t.amount / 100,
            date=datetime.fromtimestamp(
                t.transacted_at
            ).date(),  # TODO I might need to change this to datetime
        )
        for t in stripe_transactions.data
    ]

    await Transaction.create_many(transactions, db)
    transaction_refresh.completed = True
    await transaction_refresh.update(db)
