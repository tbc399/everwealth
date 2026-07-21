from datetime import datetime

from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from everwealth.accounts.models import (
    Account,
    AccountSubType,
    AccountType,
    Asset,
    PlaidItem,
)
from everwealth.auth import auth_user
from everwealth.config import settings
from everwealth.db import get_connection
from everwealth.plaid import plaid_post
from everwealth.transactions.plaid_sync import sync_item_transactions

router = APIRouter()
templates = Jinja2Templates(directory="everwealth/templates")


def _group_accounts(accounts: list[Account]) -> dict[str, list[Account]]:
    labels = {
        "cash": "Cash",
        "credit": "Credit",
        "investment": "Investment",
        "manual": "Other",
        "other": "Other",
    }
    grouped: dict[str, list[Account]] = {}
    for account in accounts:
        grouped.setdefault(labels.get(account.type, "Other"), []).append(account)
    return grouped


async def _accounts_context(user_id: str, db: Connection) -> dict:
    accounts = await Account.fetch_all(user_id, db)
    return {"accounts": accounts, "account_groups": _group_accounts(accounts)}


@router.get("/accounts", response_class=HTMLResponse)
async def get_accounts(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    context = await _accounts_context(user_id, db)
    context.update(
        {
            "request": request,
            "tab": "accounts",
            "partial": "accounts/accounts-tab.html",
            "menu_selection": "accounts",
            "title": "Connections",
        }
    )
    return templates.TemplateResponse("accounts/accounts.html", context)


@router.get("/accounts/assets", response_class=HTMLResponse)
async def get_accounts_assets(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        "accounts/accounts.html",
        {
            "request": request,
            "tab": "assets",
            "partial": "accounts/assets-tab.html",
            "assets": await Asset.fetch_all(user_id, db),
            "menu_selection": "accounts",
            "title": "Assets",
        },
    )


@router.get("/accounts/partial", response_class=HTMLResponse)
async def get_accounts_partial(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    context = await _accounts_context(user_id, db)
    context.update(
        {
            "request": request,
            "tab": "accounts",
            "partial": "accounts/accounts-tab.html",
            "title": "Connections",
        }
    )
    return templates.TemplateResponse("accounts/accounts-partial.html", context)


@router.get("/accounts/accounts-tab", response_class=HTMLResponse)
async def get_accounts_tab(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    context = await _accounts_context(user_id, db)
    context["request"] = request
    return templates.TemplateResponse("accounts/accounts-tab.html", context)


@router.get("/accounts/assets-tab", response_class=HTMLResponse)
async def get_assets_tab(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        "accounts/assets-tab.html",
        {"request": request, "assets": await Asset.fetch_all(user_id, db)},
    )


@router.post("/accounts/create-link")
async def create_link_token(user_id: str = Depends(auth_user)):
    data = await plaid_post(
        "/link/token/create",
        {
            "client_name": settings.app_name,
            "language": "en",
            "country_codes": ["US"],
            "user": {"client_user_id": user_id},
            "products": ["auth", "transactions"],
            "optional_products": ["investments", "liabilities"],
            "webhook": str(settings.plaid_webhook_handler_url),
        },
    )
    return {"link_token": data["link_token"]}


class PublicTokenRequest(BaseModel):
    public_token: str


@router.post("/accounts/exchange-token", status_code=201)
async def exchange_public_token(
    payload: PublicTokenRequest,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    exchange = await plaid_post(
        "/item/public_token/exchange", {"public_token": payload.public_token}
    )
    access_token = exchange["access_token"]
    account_data = await plaid_post("/accounts/get", {"access_token": access_token})
    item_data = account_data["item"]

    item = PlaidItem(
        user_id=user_id,
        access_token=access_token,
        institution_id=item_data.get("institution_id"),
        item_id=item_data["item_id"],
    )

    async with db.transaction():
        await item.save(db)
        for plaid_account in account_data.get("accounts", []):
            account_type = plaid_account.get("type", "other")
            if account_type not in AccountType._value2member_map_:
                account_type = "other"
            subtype = plaid_account.get("subtype") or "other"
            if subtype not in AccountSubType._value2member_map_:
                subtype = "other"
            existing_account = await Account.fetch_by_plaid_account_id(
                item.id, plaid_account["account_id"], db
            )
            account_kwargs = {"id": existing_account.id} if existing_account else {}
            account = Account(
                **account_kwargs,
                name=plaid_account["name"],
                type=account_type,
                sub_type=subtype,
                user_id=user_id,
                institution_name=item_data.get("institution_name", ""),
                last4=plaid_account.get("mask") or "",
                plaid_item_id=item.id,
                plaid_account_id=plaid_account["account_id"],
                last_sync=datetime.utcnow(),
            )
            await account.save(db)
    try:
        await sync_item_transactions(item.item_id, db)
    except HTTPException as error:
        # Plaid may still be preparing initial transaction data immediately after Link.
        logger.warning(
            "Initial Plaid transaction sync skipped for item {}: {}", item.item_id, error
        )
        pass
    return Response(status_code=201)


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_account(
    account_id: str,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    await db.execute("DELETE FROM accounts WHERE id = $1 AND user_id = $2", account_id, user_id)
    return Response(status_code=204)
