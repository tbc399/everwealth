import asyncio
import csv
from datetime import date, datetime
from typing import Annotated

from asyncpg import Connection
from dateutil import parser
from fastapi import APIRouter, Depends, Form, Request, UploadFile, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.auth import User, auth_user
from everwealth.db import get_connection
from everwealth.budgets import Category
from everwealth.transactions import (
    Account,
    Transaction,
)

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    transactions = await Transaction.fetch_many(user_id, db)
    return templates.TemplateResponse(
        request=request,
        name="transactions/transactions.html",
        context={"transactions": list(reversed(transactions)), "active_tab": "transactions"},
    )


@router.get("/transactions-partial", response_class=HTMLResponse)
async def get_transactions_partial(request: Request, conn: Connection = Depends(get_connection)):
    transactions = await Transaction.fetch_many(request.user, conn)
    return templates.TemplateResponse(
        request=request,
        name="transactions/transactions-partial.html",
        context={"transactions": reversed(transactions), "active_tab": "transactions"},
    )


@router.get("/transactions/{id}/edit", response_class=HTMLResponse)
async def get_transaction_edit_section(
    id: Annotated[str, Path(min_length=22, max_length=22)],
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    transaction = await Transaction.fetch(id, db)
    print(transaction)
    cats = await Category.fetch_many(user_id, db)
    return templates.TemplateResponse(
        request=request,
        name="transactions/edit-transaction.html",
        context={"transaction": transaction, "categories": cats},
    )


@router.put("/transactions/{id}", response_class=HTMLResponse)
async def update_transaction(
    id: Annotated[str, Path(min_length=22, max_length=22)],
    request: Request,
    description: Annotated[str, Form()],
    # amount: Annotated[float, Form()],
    date: Annotated[date, Form()],
    notes: Annotated[str, Form()] = None,
    category_id: Annotated[str, Form(alias="category")] = None,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    # TODO: need to validate input

    transaction: Transaction = await Transaction.fetch(id, db)
    transaction.description = description
    transaction.date = date
    transaction.notes = notes
    # transaction.amount = amount

    cat = await Category.fetch(category_id, user_id, db)
    # need to throw if cat is invalid
    transaction.category_id = cat.id
    transaction.category_name = cat.name

    await transaction.update(db)

    return templates.TemplateResponse(
        request=request,
        name="transactions/list-item.html",
        context={"transaction": transaction},
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
        transaction = Transaction(
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

    await Transaction.create_many(transactions, conn)

    return RedirectResponse(url="/transactions", status_code=303)  # TODO: redirect to other page


@router.get("/transactions/partial", response_class=HTMLResponse)
async def transaction_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/transactions.html")
