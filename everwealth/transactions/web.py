import asyncio
import csv
from datetime import date, datetime
from typing import Annotated

from asyncpg import Connection
from dateutil import parser
from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.auth import User, auth_user
from everwealth.db import get_connection
from everwealth.settings import categories
from everwealth.transactions import (
    Account,
    AccountTransaction,
    AccountTransactionCategoryView,
    AccountView,
    bulk_create,
    fetch,
    fetch_many,
    update,
)

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(
    request: Request, conn: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    transactions = await fetch_many(user_id, conn)
    print(transactions)
    return templates.TemplateResponse(
        request=request,
        name="transactions/transactions.html",
        context={"transactions": list(reversed(transactions)), "active_tab": "transactions"},
    )


@router.get("/transactions-partial", response_class=HTMLResponse)
async def get_transactions_partial(request: Request, conn: Connection = Depends(get_connection)):
    transactions = await fetch_many(request.user, conn)
    return templates.TemplateResponse(
        request=request,
        name="transactions/transactions-partial.html",
        context={"transactions": reversed(transactions), "active_tab": "transactions"},
    )


@router.get("/transactions/{id}/edit", response_class=HTMLResponse)
async def get_transaction_edit_section(
    id: str,
    request: Request,
    conn: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    transaction = await fetch(id, conn)
    cats = await categories.fetch_many(user_id, conn)
    return templates.TemplateResponse(
        request=request,
        name="transactions/edit-modal.html",
        context={"transaction": transaction, "categories": cats},
    )


@router.put("/transactions/{id}/edit", response_class=HTMLResponse)
async def update_transaction(
    id: str,
    request: Request,
    description: Annotated[str, Form()],
    amount: Annotated[float, Form()],
    date: Annotated[date, Form()],
    category_id: Annotated[str, Form(alias="category")] = None,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    # TODO: need to validate input

    transaction: AccountTransaction = await fetch(id, db)
    transaction.description = description
    transaction.amount = amount

    print(user_id)
    print(category_id)
    cat = await categories.fetch(category_id, user_id, db)
    transaction.category = AccountTransactionCategoryView(id=cat.id, name=cat.name)

    updated_transaction = await update(transaction, db)

    return templates.TemplateResponse(
        request=request,
        name="transactions/list-item.html",
        context={"transaction": updated_transaction},
    )


@router.post("/transactions", response_class=HTMLResponse)
async def create_transaction(request: Request, conn: Connection = Depends(get_connection)):
    return


@router.get("/transactions/upload", response_class=HTMLResponse)
async def get_upload_modal(request: Request, db: Connection = Depends(get_connection)):
    return templates.TemplateResponse(
        request=request,
        name="transactions/upload-modal.html",
    )


@router.post("/transactions/upload", response_class=HTMLResponse)
async def upload_transactions(
    request: Request,
    file: UploadFile,
    conn: Connection = Depends(get_connection),
    user_id: User = Depends(auth_user),
):
    # TODO: provide a form for user to map their upload file headers to the acceptable ones.

    text_file = (line.decode("utf-8") for line in file.file)
    reader = csv.DictReader(text_file)
    # header = next(reader)
    # validate the header
    # reader.fieldnames

    transactions = []

    # TODO: need to get the account

    for line in reader:
        print(line)
        transaction = AccountTransaction(
            user_id=user_id,
            account=None,
            description=line["Description"],
            amount=line["Amount"],
            # date=datetime.strptime(line["Date"], "%Y-%M-%d").date(),
            date=parser.parse(line["Date"]).date(),
        )
        transaction.hash()
        transactions.append(transaction)

    # TODO: need to check hashes so as not to duplicate

    await bulk_create(transactions, conn)

    return RedirectResponse(url="/transactions", status_code=303)  # TODO: redirect to other page


@router.get("/transactions/partial", response_class=HTMLResponse)
async def transaction_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/transactions.html")
