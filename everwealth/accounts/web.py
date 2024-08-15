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
from everwealth.accounts import Account
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
    # the to level accounts page should land on the "Banking" tab
    accounts = await Account.fetch_by_type(user_id, "cash", db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts.html",
        context={
            "accounts": accounts,
            "menu_tab": "accounts",
            "title": "Accounts",
            "partial_template": "accounts/accounts-partial.html",
            "partial_endpoint": "accounts/partial",
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
            "accounts": accounts,
            "active_tab": "banking-tab",
            "title": "Accounts",
            "stripe_pub_key": settings.stripe_pub_key,
        },
    )


@router.get("/accounts/banking", response_class=HTMLResponse)
async def get_accounts_banking(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, "banking", db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/list-partial.html",
        context={
            "accounts": accounts,
            "account_type": "banking",
            "active_tab": "banking-tab",
            "title": "Accounts",
        },
    )


@router.get("/accounts/debts", response_class=HTMLResponse)
async def get_accounts_debts(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, "debt", db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/list-partial.html",
        context={
            "accounts": accounts,
            "account_type": "debts",
            "active_tab": "debts-tab",
            "title": "Accounts",
        },
    )


@router.get("/accounts/investments", response_class=HTMLResponse)
async def get_accounts_investments(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, "investment", db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/list-partial.html",
        context={
            "accounts": accounts,
            "account_type": "investments",
            "active_tab": "investments-tab",
            "title": "Accounts",
        },
    )


@router.get("/accounts/assets", response_class=HTMLResponse)
async def get_accounts_assets(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    accounts = await Account.fetch_all(user_id, "asset", db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/list-partial.html",
        context={
            "accounts": accounts,
            "account_type": "assets",
            "active_tab": "assets-tab",
            "title": "Accounts",
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
