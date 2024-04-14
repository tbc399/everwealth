from datetime import datetime
import asyncio
import csv
from fastapi import UploadFile
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.transactions import AccountTransaction, bulk_create, Account
from everwealth.db import get_connection
from fastapi import Depends
from everwealth.transactions import fetch_many

from everwealth.users import User

from asyncpg import Connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(request: Request, conn: Connection = Depends(get_connection)):
    # request.user
    user = User(email="traviscammack@protonmail.com")
    transactions = await fetch_many(user, conn)
    print(transactions)
    return templates.TemplateResponse(
        request=request, name="transactions.html", context={"transactions": transactions}
    )


@router.post("/transactions", response_class=HTMLResponse)
async def create_transaction(request: Request, conn: Connection = Depends(get_connection)):
    return


@router.post("/transactions/upload", response_class=HTMLResponse)
async def upload_transactions(
    request: Request, file: UploadFile, conn: Connection = Depends(get_connection)
):
    text_file = (line.decode("utf-8") for line in file.file)
    reader = csv.DictReader(text_file)
    # header = next(reader)
    # validate the header
    # reader.fieldnames


    transactions = []

    # need to get the account
    account = Account(user=User(email="traviscammack@protonmail.com"))

    for line in reader:
        transactions.append(AccountTransaction(
            account=account,
            description=line["Description"],
            amount=line["Amount"],
            date=datetime.strptime(line["Date"], "%Y-%M-%d"),
        ))

    await bulk_create(transactions, conn)

    return RedirectResponse(url="/transactions", status_code=303)  # TODO: redirect to other page


@router.get("/transactions/partial", response_class=HTMLResponse)
async def transaction_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/transactions.html")
