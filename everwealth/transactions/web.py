import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Annotated, Optional

from asyncpg import Connection
from dateutil import parser
from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from everwealth.accounts import Account
from everwealth.auth import auth_user
from everwealth.budgets import Category
from everwealth.db import get_connection
from everwealth.transactions import Transaction, TransactionRule

router = APIRouter()
templates = Jinja2Templates(directory="everwealth/templates")


def _group_by_date(transactions: list[Transaction]) -> list[tuple]:
    groups = defaultdict(list)
    for transaction in transactions:
        groups[transaction.date].append(transaction)
    return sorted(groups.items(), key=lambda item: item[0], reverse=True)


async def _transaction_context(
    user_id: str, db: Connection, account_id: Optional[str] = None
) -> dict:
    transactions = await Transaction.fetch_many(user_id, db, account_id)
    return {
        "transactions": transactions,
        "transaction_groups": _group_by_date(transactions),
        "accounts": await Account.fetch_all(user_id, db),
        "selected_account": account_id,
    }


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(
    request: Request,
    account: Optional[str] = None,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    context = await _transaction_context(user_id, db, account)
    context.update(
        {
            "request": request,
            "tab": "transactions",
            "partial": "transactions/transactions-tab.html",
            "menu_selection": "transactions",
            "title": "Transactions",
        }
    )
    return templates.TemplateResponse("transactions/transactions.html", context)


@router.get("/transactions/partial", response_class=HTMLResponse)
async def get_transactions_partial(
    request: Request,
    account: Optional[str] = None,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    context = await _transaction_context(user_id, db, account)
    context.update(
        {"request": request, "tab": "transactions", "partial": "transactions/transactions-tab.html"}
    )
    return templates.TemplateResponse("transactions/transactions-partial.html", context)


@router.get("/transactions/transactions-tab", response_class=HTMLResponse)
async def get_transactions_tab(
    request: Request,
    account: Optional[str] = None,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    context = await _transaction_context(user_id, db, account)
    context["request"] = request
    return templates.TemplateResponse("transactions/transactions-tab.html", context)


@router.get("/transactions/rules", response_class=HTMLResponse)
@router.get("/transactions/rules-tab", response_class=HTMLResponse)
async def get_transaction_rules(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        "transactions/rules-tab.html",
        {"request": request, "rules": await TransactionRule.fetch_many(user_id, db)},
    )


@router.get("/transactions/upload", response_class=HTMLResponse)
async def get_upload_modal(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        "transactions/upload-modal.html",
        {"request": request, "accounts": await Account.fetch_all(user_id, db)},
    )


@router.post("/transactions/upload")
async def upload_transactions(
    file: UploadFile,
    account: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    valid_account = await db.fetchval(
        "SELECT EXISTS(SELECT 1 FROM accounts WHERE id = $1 AND user_id = $2)", account, user_id
    )
    if not valid_account:
        raise HTTPException(status_code=400, detail="Invalid account")
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content))
    normalized = {name.lower(): name for name in (reader.fieldnames or [])}
    required = {"date", "description", "amount"}
    if not required.issubset(normalized):
        raise HTTPException(
            status_code=400, detail="CSV needs Date, Description, and Amount columns"
        )
    transactions = []
    for row_number, row in enumerate(reader, start=2):
        try:
            amount = int(Decimal(row[normalized["amount"]].replace(",", "").replace("$", "")) * 100)
            trans_date = parser.parse(row[normalized["date"]]).date()
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid CSV row {row_number}") from exc
        transactions.append(
            Transaction(
                user_id=user_id,
                account_id=account,
                description=row[normalized["description"]].strip(),
                amount=amount,
                date=trans_date,
            )
        )
    await Transaction.create_many(transactions, db)
    return RedirectResponse("/transactions", status_code=303)


@router.get("/transactions/{transaction_id}", response_class=HTMLResponse)
@router.get("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
async def get_transaction_edit(
    transaction_id: Annotated[str, Path()],
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    transaction = await Transaction.fetch(transaction_id, user_id, db)
    if not transaction:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "transactions/edit-transaction.html",
        {
            "request": request,
            "transaction": transaction,
            "categories": await Category.fetch_many(user_id, db),
        },
    )


@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    description: Annotated[str, Form()],
    date: Annotated[date, Form()],
    notes: Annotated[Optional[str], Form()] = None,
    category_id: Annotated[Optional[str], Form(alias="category")] = None,
    hidden: Annotated[bool, Form()] = False,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    transaction = await Transaction.fetch(transaction_id, user_id, db)
    if not transaction:
        raise HTTPException(status_code=404)
    if category_id and not await Category.fetch(category_id, user_id, db):
        raise HTTPException(status_code=400, detail="Invalid category")
    transaction.description = description
    transaction.date = date
    transaction.notes = notes or None
    transaction.category_id = category_id
    transaction.hidden = hidden
    await transaction.save(db)
    return Response(status_code=200, headers={"HX-Redirect": "/transactions"})
