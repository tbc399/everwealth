from collections import defaultdict
from datetime import datetime
from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth import transactions
from everwealth.accounts import Account
from everwealth.auth import auth_user
from everwealth.budgets import Budget, BudgetMonthsView, BudgetView, Category
from everwealth.db import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/accounts", response_class=HTMLResponse)
async def get_accounts(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    #accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts.html",
        context={
            "accounts": [],
            "active_tab": "accounts",
            "title": "Accounts",
            "partial_template": "accounts/accounts-partial.html",
            "partial_endpoint": "accounts/partial",
        },
    )


@router.get("/accounts/partial", response_class=HTMLResponse)
async def get_accounts_partial(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    #accounts = await Account.fetch_all(user_id, db)

    return templates.TemplateResponse(
        request=request,
        name="accounts/accounts-partial.html",
        context={
            "accounts": [],
            "active_tab": "accounts",
            "title": "Accounts",
            "partial_template": "accounts/accounts-partial.html",
            "partial_endpoint": "accounts/partial",
        },
    )
