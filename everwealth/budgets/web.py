from datetime import datetime
from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response
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
from everwealth.budgets.models.categories import CategoryType
from everwealth.transactions import Transaction

router = APIRouter()
templates = Jinja2Templates(directory="everwealth/templates")


async def _selected_period(user_id: str, db: Connection, month: str = "") -> BudgetPeriod:
    if month:
        try:
            selected = datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=422, detail="Month must be YYYY-MM") from None
    period = await BudgetPeriod.current(user_id, db)
    if month:
        period = await BudgetPeriod.fetch_for_month(user_id, selected.year, selected.month, db)
        if not period:
            raise HTTPException(status_code=404, detail="No budget period for this month")
    return period


async def _budget_context(user_id: str, db: Connection, month: str = "") -> dict:
    period = await _selected_period(user_id, db, month)
    return {
        "budgets": await BudgetView.fetch_all_by_month(
            user_id, period.start.year, period.start.month, db
        ),
        "overview": await BudgetOverview.fetch(user_id, period, db),
        "period": period,
        "months": await BudgetPeriod.timeline(user_id, db),
    }


@router.get("/budgets", response_class=HTMLResponse)
async def get_budgets(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user),
    month: str = "",
):
    context = await _budget_context(user_id, db, month)
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
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user),
    month: str = "",
):
    context = await _budget_context(user_id, db, month)
    context.update({"request": request, "active_tab": "budgets"})
    return templates.TemplateResponse("budgets/budgets-partial.html", context)


@router.get("/budgets/create", response_class=HTMLResponse)
async def get_budget_create(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user),
    month: str = "",
):
    period = await _selected_period(user_id, db, month)
    return templates.TemplateResponse(
        "budgets/create-modal.html",
        {"request": request, "category_groups": await Category.fetch_grouped(user_id, db),
         "period": period},
    )


@router.post("/budgets")
async def create_budget(
    category_id: Annotated[str, Form(alias="category")],
    amount: Annotated[int, Form(ge=0)],
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
    month: Annotated[str, Form()] = "",
):
    if not await Category.fetch(category_id, user_id, db):
        raise HTTPException(status_code=400, detail="Invalid category")
    period = await _selected_period(user_id, db, month)
    if await db.fetchrow(
        "SELECT id FROM budgets WHERE period_id = $1 AND category_id = $2", period.id, category_id
    ):
        raise HTTPException(status_code=409, detail="Category already has a budget")
    await Budget(
        period_id=period.id,
        user_id=user_id,
        category_id=category_id,
        amount=amount,
    ).save(db)
    return RedirectResponse(f"/budgets?month={period.start:%Y-%m}", status_code=303)


@router.get("/budgets/income/edit", response_class=HTMLResponse)
async def get_income_edit(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user),
    month: str = "",
):
    context = await _budget_context(user_id, db, month)
    context.update({
        "request": request,
        "income_categories": [
            category for category in await Category.fetch_many(user_id, db)
            if category.type == "income" and not category.parent_id
            and category.name.casefold() == "income"
        ],
        "budgets_by_category": {
            budget["category_id"]: budget for budget in await db.fetch(
                "SELECT id, category_id, amount FROM budgets WHERE user_id = $1 AND period_id = $2",
                user_id, context["period"].id,
            )
        },
    })
    return templates.TemplateResponse("budgets/edit-income.html", context)


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
        {"request": request, "budget": budget, "transactions": transactions,
         "month": period["start"].strftime("%Y-%m")},
    )


@router.put("/budgets/{budget_id}")
async def update_budget(
    budget_id: str,
    amount: Annotated[int, Form(ge=0)],
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
    month: Annotated[str, Form(pattern=r"^$|^\d{4}-(0[1-9]|1[0-2])$")] = "",
):
    budget = await Budget.fetch(budget_id, user_id, db)
    if not budget:
        raise HTTPException(status_code=404)
    budget.amount = amount
    await budget.save(db)
    return Response(status_code=200, headers={"HX-Redirect": f"/budgets?month={month}" if month else "/budgets"})


@router.delete("/budgets/{budget_id}")
async def delete_budget(
    budget_id: str, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user),
    month: Annotated[str, Query(pattern=r"^$|^\d{4}-(0[1-9]|1[0-2])$")] = "",
):
    await db.execute("DELETE FROM budgets WHERE id = $1 AND user_id = $2", budget_id, user_id)
    return Response(status_code=200, headers={"HX-Redirect": f"/budgets?month={month}" if month else "/budgets"})


@router.get("/categories", response_class=HTMLResponse)
async def get_categories(
    request: Request, db: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    return templates.TemplateResponse(
        "budgets/budgets.html",
        {
            "request": request,
            "active_tab": "categories",
            "category_groups": await Category.fetch_grouped(user_id, db),
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
            "category_groups": await Category.fetch_grouped(user_id, db),
        },
    )


@router.post("/categories")
async def create_category(
    name: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
    parent_id: Annotated[str, Form()] = "",
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Category name is required")
    parent = await Category.fetch(parent_id, user_id, db) if parent_id else None
    if parent_id and (not parent or parent.parent_id):
        raise HTTPException(status_code=400, detail="Choose a valid main category")
    if any(category.name.casefold() == name.casefold()
           for category in await Category.fetch_many(user_id, db)):
        raise HTTPException(status_code=409, detail="Category already exists")
    await Category.create(
        name, user_id, db,
        type=parent.type if parent else CategoryType.expense,
        parent_id=parent.id if parent else None,
    )
    return RedirectResponse("/categories", status_code=303)
