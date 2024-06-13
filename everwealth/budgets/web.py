from typing import Annotated
from collections import defaultdict
from everwealth.auth import auth_user
from datetime import datetime

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.budgets import Budget, fetch, fetch_all_by_month, create, BudgetCategoryView
from everwealth import transactions
from everwealth.settings import categories
from everwealth.db import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/budgets", response_class=HTMLResponse)
async def create_budget(
    request: Request,
    category_id: Annotated[str, Form(alias="category")],
    amount: Annotated[int, Form()],
    frequency: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    cat = await categories.fetch(category_id, user_id, db)
    budget = Budget(
        user_id=user_id,
        category=BudgetCategoryView(id=category_id, name=cat.name),
        amount=amount,
        frequency=frequency,
    )
    _ = await create(budget, db)
    return RedirectResponse(url="/budgets", status_code=303)  # TODO: redirect to other page


@router.get("/budgets/{id}/edit", response_class=HTMLResponse)
async def get_edit_budget(
    request: Request,
    id: str,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    budget = await fetch(id, user_id, db)
    return templates.TemplateResponse(
        request=request, name="budgets/edit-budget.html", context={"budget": budget}
    )


@router.get("/new_budget", response_class=HTMLResponse)
async def get_create_budget_form(request: Request):
    return templates.TemplateResponse(request=request, name="new-budget.html")


@router.get("/budgets/create", response_class=HTMLResponse)
async def get_budget_create_modal(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    cats = await categories.fetch_many(user_id, db)
    return templates.TemplateResponse(
        request=request, name="budgets/create-modal.html", context={"categories": cats}
    )


@router.get("/budgets", response_class=HTMLResponse)
async def budgets(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    now = datetime.utcnow()
    budgets = await fetch_all_by_month(user_id, now.year, now.month, db)
    budget_names = set(_.category.name for _ in budgets)
    budget_sums = defaultdict(float)

    # trans = await transactions.fetch_many_by_month(user_id, month, db)
    trans = await transactions.fetch_many(user_id, db)

    for transaction in trans:
        if transaction.category.name in budget_names:
            budget_sums[transaction.category.name] += transaction.amount

    return templates.TemplateResponse(
        request=request,
        name="budgets/budgets.html",
        context={"budgets": budgets, "budget_sums": budget_sums, "active_tab": "budgets"},
    )


@router.get("/budgets/partial", response_class=HTMLResponse)
async def budgets_partial(request: Request):
    return templates.TemplateResponse(
        request=request, name="budgets/budgets-partial.html", context={"active_tab": "budgets"}
    )
