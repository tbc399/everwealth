import stripe
from fastapi import BackgroundTasks, Request
from fastapi.routing import APIRouter, Response
from loguru import logger
from pydantic import BaseModel

from everwealth import db
from everwealth.accounts import Account
from everwealth.auth import User
from everwealth.config import settings
from everwealth.transactions import TransactionRefresh, refresh_scheduler
from everwealth.transactions.plaid_sync import sync_item_transactions

router = APIRouter()


class PlaidWebhook(BaseModel):
    webhook_type: str
    webhook_code: str
    item_id: str | None = None
    error: dict | None = None
    environment: str | None = None
    new_transactions: int | None = None
    initial_update_complete: bool | None = None
    historical_update_complete: bool | None = None


async def handle_transactions_refresh_event(event):
    async with db.pool.acquire() as connection:
        # user = await User.fetch_by_stripe_id(event.data.object.account_holder.customer, connection)
        # account = await Account.fetch_by_user_id(user.id, connection)
        await refresh_scheduler.refresh(
            event.data.object.transaction_refresh.id, event.data.object.id, connection
        )


async def handle_plaid_transaction_webhook(item_id: str):
    async with db.pool.acquire() as connection:
        await sync_item_transactions(item_id, connection)


@router.post("/transactions/hooks/refresh")
async def account_transaction_refresh_handler(request: Request, tasks: BackgroundTasks):
    signature = request.headers.get("stripe-signature")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_signing_secret)
        logger.info(f"recieved Stripe event {event.id} of type {event.type}")
    except ValueError as error:
        logger.error(f"failed to parse Stripe event payload: {error}")
        return Response(status_code=400)

    if event.type != "financial_connections.account.refreshed_transactions":
        return Response(status_code=400)

    tasks.add_task(handle_transactions_refresh_event, event)
    return Response(status_code=200)


@router.post("/transactions/hooks/plaid")
async def plaid_transaction_webhook_handler(payload: PlaidWebhook, tasks: BackgroundTasks):
    logger.info(
        "received Plaid webhook type={} code={} item_id={}",
        payload.webhook_type,
        payload.webhook_code,
        payload.item_id,
    )

    if payload.webhook_type != "TRANSACTIONS":
        return Response(status_code=200)

    if payload.error:
        logger.warning(
            "Plaid transactions webhook returned error for item {}: {}",
            payload.item_id,
            payload.error,
        )

    if not payload.item_id:
        return Response(status_code=400)

    sync_webhook_codes = {
        "SYNC_UPDATES_AVAILABLE",
        "INITIAL_UPDATE",
        "HISTORICAL_UPDATE",
        "DEFAULT_UPDATE",
        "TRANSACTIONS_REMOVED",
    }
    if payload.webhook_code in sync_webhook_codes:
        tasks.add_task(handle_plaid_transaction_webhook, payload.item_id)

    return Response(status_code=200)
