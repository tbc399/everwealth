import json
from collections import defaultdict
from datetime import datetime
from typing import Annotated

import stripe
from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from everwealth import transactions
from everwealth.accounts import Account, Asset
from everwealth.auth import User, auth_user
from everwealth.budgets import Budget, BudgetMonthsView, BudgetView, Category
from everwealth.config import settings
from everwealth.db import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


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
            "partial": "accounts/accounts-tab.html",
            "accounts": accounts,
            "menu_tab": "accounts",
            "title": "Accounts",
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
            "partial": "accounts/assets-tab.html",
            "assets": assets,
            "menu_tab": "accounts",
            "title": "Assets",
            "stripe_pub_key": settings.stripe_pub_key,
        },
    )


@router.get("/accounts/partial", response_class=HTMLResponse)
async def get_accounts_partial(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts-partial.html",
        context={
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

    header = {"accountsTabChanged": {"target": "#accounts-tab-group", "tab_id": "accounts-tab"}}
    return templates.TemplateResponse(
        request=request,
        headers={"HX-Trigger": json.dumps(header)},
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
    assets = [] #await Asset.fetch_all(user_id, db)

    header = {"accountsTabChanged": {"target": "#accounts-tab-group", "tab_id": "assets-tab"}}
    return templates.TemplateResponse(
        request=request,
        headers={"HX-Trigger": json.dumps(header)},
        name=f"accounts/{'assets-tab' if assets else 'assets-tab-empty'}.html",
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


@router.get("/accounts/create", response_class=HTMLResponse)
async def get_accounts_create_modal(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts-create-modal.html",
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
