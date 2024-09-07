import json

import stripe
from asyncpg import Connection
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from everwealth.accounts import Account, Asset
from everwealth.auth import User, auth_user
from everwealth.budgets import Budget, BudgetMonthsView, BudgetView
from everwealth.config import settings
from everwealth.db import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


# Top level routes
@router.get("/accounts", response_class=HTMLResponse)
async def get_accounts(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    # the top level accounts page should land on the "Accounting" tab
    accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts.html",
        context={
            "tab": "accounts",
            "partial": "accounts/accounts-tab.html",
            "accounts": accounts,
            "menu_selection": "accounts",
            "stripe_pub_key": settings.stripe_pub_key,
        },
    )


@router.get("/accounts/assets", response_class=HTMLResponse)
async def get_accounts_assets(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    assets = await Asset.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts.html",
        context={
            "tab": "assets",
            "partial": "accounts/assets-tab.html",
            "assets": assets,
            "menu_selection": "accounts",
            "title": "Assets",
            "stripe_pub_key": settings.stripe_pub_key,
        },
    )


# End top level routes


@router.get("/accounts/partial", response_class=HTMLResponse)
async def get_accounts_partial(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts-partial.html",
        context={
            "tab": "accounts",
            "partial": "accounts/accounts-tab.html",
            "accounts": accounts,
            "active_tab": "accounts-tab",
            "title": "Accounts",
            "stripe_pub_key": settings.stripe_pub_key,
        },
    )


@router.get("/accounts/accounts-tab", response_class=HTMLResponse)
async def get_accounts_tab(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts-tab.html",
        context={
            "accounts": accounts,
            "active_tab": "accounts-tab",
            "title": "Accounts",
        },
    )


@router.get("/accounts/assets-tab", response_class=HTMLResponse)
async def get_assets_tab(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    assets = []  # await Asset.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/assets-tab.html",
        context={
            "assets": assets,
            "active_tab": "assets-tab",
            "title": "Assets",
        },
    )


@router.get("/accounts/partial/list", response_class=HTMLResponse)
async def get_accounts_partial_list(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/list-partial.html",
        context={"accounts": accounts},
    )


@router.get("/accounts/connect")
async def connect_account(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    user = await User.fetch(user_id, db)
    fc_session = await stripe.financial_connections.Session.create_async(
        account_holder={"type": "customer", "customer": user.stripe_customer_id},
        permissions=["balances", "transactions"],
    )
    return {"client_secret": fc_session["client_secret"]}


@router.delete("/accounts/{id}")
async def disconnect_account(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return Response(status_code=204)
