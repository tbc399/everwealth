import stripe
from fastapi import BackgroundTasks, Request
from fastapi.routing import APIRouter, Response
from loguru import logger

from everwealth import db
from everwealth.accounts import Account
from everwealth.auth import User
from everwealth.config import settings
from everwealth.transactions import TransactionRefresh, refresh_scheduler

router = APIRouter()


async def handle_transactions_refresh_event(event):
    async with db.pool.acquire() as connection:
        # user = await User.fetch_by_stripe_id(event.data.object.account_holder.customer, connection)
        # account = await Account.fetch_by_user_id(user.id, connection)
        await refresh_scheduler.refresh(
            event.data.object.transaction_refresh.id, event.data.object.id, connection
        )


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
