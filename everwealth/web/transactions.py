from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from everwealth.models import AccountTransaction

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(request: Request):
    transactions = [
        AccountTransaction(
            date=datetime.now(),
            description="Some stuff",
            amount=12.34,
            category="Groceries",
            notes="asdfasdf",
        ),
        AccountTransaction(
            date=datetime.now(),
            description="Water bill",
            amount=34.34,
            category="Water",
            notes="asdfasdf",
        ),
        AccountTransaction(
            date=datetime.now(),
            description="Costco gas",
            amount=45.00,
            category="Gasoline",
            notes="Some notes",
        ),
        AccountTransaction(
            date=datetime.now(),
            description="Costco Wholesale",
            amount=266.34,
            category="Groceries",
            notes="Some notes",
        ),
        AccountTransaction(
            date=datetime.now(),
            description="Reliant",
            amount=120.87,
            category="Electricity",
            notes="Some notes",
        ),
    ]
    return templates.TemplateResponse(
        request=request, name="transactions.html", context={"transactions": transactions}
    )


@router.get("/transaction_section", response_class=HTMLResponse)
async def transaction_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/transactions.html")
