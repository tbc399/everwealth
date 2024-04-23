import asyncio
import csv
from datetime import datetime, date
from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.db import get_connection
from everwealth.transactions import (
    Account,
    AccountTransaction,
    bulk_create,
    fetch,
    fetch_many,
    update
)
from everwealth.users import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(request: Request, conn: Connection = Depends(get_connection)):
    # request.user
    user = User(email="traviscammack@protonmail.com")
    transactions = await fetch_many(None, conn)
    return templates.TemplateResponse(
        request=request,
        name="transactions.html",
        context={"transactions": reversed(transactions), "active_tab": "transactions"},
    )


@router.get("/transactions/{id}/edit", response_class=HTMLResponse)
async def get_transaction_edit_section(
    id: str, request: Request, conn: Connection = Depends(get_connection)
):
    transaction = await fetch(id, conn)
    return templates.TemplateResponse(
        request=request, name="partials/transaction-edit.html", context={"transaction": transaction}
    )


@router.put("/transactions/{id}/edit", response_class=HTMLResponse)
async def update_transaction(
    id: str,
    request: Request,
    description: Annotated[str, Form()],
    amount: Annotated[float, Form()],
    date: Annotated[date, Form()],
    category: Annotated[str, Form()] = None,
    conn: Connection = Depends(get_connection),
):

    transaction: AccountTransaction = await fetch(id, conn)

    # TODO: need to validate input

    transaction.description = description
    # transaction.category = category
    transaction.amount = amount

    updated_transaction = await update(transaction, conn)

    return templates.TemplateResponse(
        request=request,
        name="partials/transaction-list-item.html",
        context={"transaction": updated_transaction},
    )


@router.post("/transactions", response_class=HTMLResponse)
async def create_transaction(request: Request, conn: Connection = Depends(get_connection)):
    return


@router.post("/transactions/upload", response_class=HTMLResponse)
async def upload_transactions(
    request: Request, file: UploadFile, conn: Connection = Depends(get_connection)
):
    # TODO: provide a form for user to map their upload file headers to the acceptable ones.

    text_file = (line.decode("utf-8") for line in file.file)
    reader = csv.DictReader(text_file)
    # header = next(reader)
    # validate the header
    # reader.fieldnames

    transactions = []

    # need to get the account
    user = User(email="traviscammack@protonmail.com")
    account = Account(user=user.id)

    for line in reader:
        transactions.append(
            AccountTransaction(
                user=user.id,
                account=account,
                description=line["Description"],
                amount=line["Amount"],
                date=datetime.strptime(line["Date"], "%Y-%M-%d").date(),
            )
        )

    await bulk_create(transactions, conn)

    return RedirectResponse(url="/transactions", status_code=303)  # TODO: redirect to other page


@router.get("/transactions/partial", response_class=HTMLResponse)
async def transaction_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/transactions.html")
