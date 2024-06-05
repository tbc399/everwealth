from typing import Annotated
from everwealth.auth import auth_user

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.budgets import Budget, fetch_many
from everwealth.db import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/budgets", response_class=HTMLResponse)
async def create_budget(
    request: Request,
    category: Annotated[str, Form()],
    amount: Annotated[int, Form()],
    conn: Connection = Depends(get_connection),
):
    print(category)
    print(amount)
    return RedirectResponse(url="/budgets-v2", status_code=303)  # TODO: redirect to other page


@router.get("/new_budget", response_class=HTMLResponse)
async def get_create_budget_form(request: Request):
    return templates.TemplateResponse(request=request, name="new-budget.html")


@router.get("/budgets/create", response_class=HTMLResponse)
async def get_budget_create_modal(
    request: Request,
    conn: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        request=request,
        name="budgets/create-modal.html",
    )

@router.get("/budgets", response_class=HTMLResponse)
async def budgets(request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)):
    #budgets = [
    #    Budget(
    #        category="Groceries",
    #        amount=40,
    #        spent=40,
    #    ),
    #    Budget(category="Gas", amount=23, spent=11),
    #    Budget(category="Home School", amount=100, spent=98),
    #    Budget(category="Entertainment", amount=55, spent=50),
    #    Budget(category="Date Night", amount=100, spent=10),
    #    Budget(category="Water", amount=75, spent=45),
    #    Budget(category="Pet", amount=90, spent=23),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #    Budget(category="Tiingo", amount=10, spent=5),
    #]
    budgets = await fetch_many(user_id, db)
    return templates.TemplateResponse(
        request=request,
        name="budgets/budgets.html",
        context={"budgets": budgets, "active_tab": "budgets"},
    )


@router.get("/budgets/partial", response_class=HTMLResponse)
async def budgets_partial(request: Request):
    return templates.TemplateResponse(
        request=request, name="budgets/budgets-partial.html", context={"active_tab": "budgets"}
    )
