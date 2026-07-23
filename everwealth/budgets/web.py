from datetime import datetime
from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.auth import auth_user
from everwealth.budgets import (
    Budget,
    BudgetOverview,
    BudgetPeriod,
    BudgetView,
    Category,
)
from everwealth.db import get_connection
from everwealth.transactions import Transaction

router = APIRouter()
templates = Jinja2Templates(directory="everwealth/templates")


async def _budget_context(user_id: str, db: Connection) -> dict:
    now = datetime.utcnow()
    period = await BudgetPeriod.current(user_id, db)
    return {
        "budgets": await BudgetView.fetch_all_by_month(user_id, now.year, now.month, db),
        "overview": await BudgetOverview.fetch(user_id, period, db),
        "period": period,
    }


@router.get("/budgets", response_class=HTMLResponse)
async def get_budgets(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    context = await _budget_context(user_id, db)
    context.update(
        {
            "request": request,
            "active_tab": "budgets",
            "title": "Budgets",
            "menu_selection": "budgets",
            "partial_endpoint": "/budgets/partial",
        }
    )
    return templates.TemplateResponse("budgets/budgets.html", context)


@router.get("/budgets/partial", response_class=HTMLResponse)
async def budgets_partial(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    context = await _budget_context(user_id, db)
    context.update({"request": request, "active_tab": "budgets"})
    return templates.TemplateResponse("budgets/budgets-partial.html", context)


@router.get("/budgets/create", response_class=HTMLResponse)
async def get_budget_create(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        "budgets/create-modal.html",
        {"request": request, "categories": await Category.fetch_many(user_id, db)},
    )


@router.post("/budgets")
async def create_budget(
    category_id: Annotated[str, Form(alias="category")],
    amount: Annotated[int, Form()],
    rollover: Annotated[bool, Form()] = False,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    if not await Category.fetch(category_id, user_id, db):
        raise HTTPException(status_code=400, detail="Invalid category")
    period = await BudgetPeriod.current(user_id, db)
    if await db.fetchrow(
        "SELECT id FROM budgets WHERE period_id = $1 AND category_id = $2", period.id, category_id
    ):
        raise HTTPException(status_code=409, detail="Category already has a budget")
    await Budget(
        period_id=period.id,
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        rollover=rollover,
    ).save(db)
    return RedirectResponse("/budgets", status_code=303)


@router.get("/budgets/{budget_id}", response_class=HTMLResponse)
@router.get("/budgets/{budget_id}/edit", response_class=HTMLResponse)
async def get_budget_detail(
    budget_id: str,
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    budget = await BudgetView.fetch(budget_id, user_id, db)
    if not budget:
        raise HTTPException(status_code=404)
    period = await db.fetchrow(
        "SELECT p.* FROM budget_periods p JOIN budgets b ON b.period_id = p.id WHERE b.id = $1 AND b.user_id = $2",
        budget_id,
        user_id,
    )
    transactions = await Transaction.fetch_for_category_in_range(
        user_id, budget.category_id, period["start"].date(), period["end"].date(), db
    )
    return templates.TemplateResponse(
        "budgets/edit-budget.html",
        {"request": request, "budget": budget, "transactions": transactions},
    )


@router.put("/budgets/{budget_id}")
async def update_budget(
    budget_id: str,
    amount: Annotated[int, Form()],
    rollover: Annotated[bool, Form()] = False,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    budget = await Budget.fetch(budget_id, user_id, db)
    if not budget:
        raise HTTPException(status_code=404)
    budget.amount = amount
    budget.rollover = rollover
    await budget.save(db)
    return Response(status_code=200, headers={"HX-Redirect": "/budgets"})


@router.delete("/budgets/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: str, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    await db.execute("DELETE FROM budgets WHERE id = $1 AND user_id = $2", budget_id, user_id)
    return Response(status_code=204)


@router.get("/categories", response_class=HTMLResponse)
async def get_categories(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        "budgets/budgets.html",
        {
            "request": request,
            "active_tab": "categories",
            "categories": await Category.fetch_many(user_id, db),
            "title": "Categories",
            "menu_selection": "budgets",
            "partial_endpoint": "/categories/partial",
        },
    )


@router.get("/categories/partial", response_class=HTMLResponse)
async def categories_partial(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        "budgets/categories-partial.html",
        {
            "request": request,
            "active_tab": "categories",
            "categories": await Category.fetch_many(user_id, db),
        },
    )


@router.post("/categories")
async def create_category(
    name: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    await Category.create(name, user_id, db)
    return RedirectResponse("/categories", status_code=303)
