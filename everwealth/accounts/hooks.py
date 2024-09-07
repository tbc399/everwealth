from datetime import datetime

import stripe
from asyncpg import Connection
from fastapi import BackgroundTasks, Depends, Request, Response
from fastapi.routing import APIRouter
from loguru import logger

from everwealth import db
from everwealth.accounts import Account
from everwealth.auth import User
from everwealth.config import settings
from everwealth.db import get_connection
from everwealth.transactions import refresh_scheduler

router = APIRouter()


async def create_account(event):
    async with db.pool.acquire() as connection:
        last4 = event.data.object.last4
        name = event.data.object.display_name
        institution_name = event.data.object.institution_name
        account_exists = await Account.already_exists(last4, institution_name, name, connection)
        if account_exists:
            logger.warning("Connected account already exists")
            return
        user = await User.fetch_by_stripe_id(event.data.object.account_holder.customer, connection)
        new_account = Account(
            name=event.data.object.display_name,
            type=event.data.object.category,
            sub_type=event.data.object.subcategory,
            user_id=user.id,
            stripe_id=event.data.object.id,
            last_sync=datetime.utcnow(),
            institution_name=event.data.object.institution_name,
            last4=event.data.object.last4,
        )
        await new_account.save(connection)
        logger.info(f"New account {new_account.id} created for user {user.id}")

        await refresh_scheduler.schedule(user, new_account, connection)


@router.post("/accounts/hooks/create")
async def create_account_handler(request: Request, tasks: BackgroundTasks):
    signature = request.headers.get("stripe-signature")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_signing_secret)
        logger.info(f"recieved Stripe event {event.type}")
    except ValueError as error:
        logger.error(f"failed to parse Stripe event payload: {error}")
        return Response(status_code=400)

    if event.type != "financial_connections.account.created":
        return Response(status_code=400)

    tasks.add_task(create_account, event)
    return Response(status_code=200)
