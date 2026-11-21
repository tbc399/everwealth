from asyncpg import Connection
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.auth import auth_user
from everwealth.accounts import Account
from everwealth.budgets import BudgetOverview, BudgetPeriod
from everwealth.db import get_connection
from everwealth.transactions import Transaction

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


async def _dashboard_context(user_id: str, conn: Connection) -> dict:
    period = await BudgetPeriod.current(user_id, conn)
    return {
        "period": period,
        "overview": await BudgetOverview.fetch(user_id, period, conn),
        "transactions": await Transaction.fetch_many(user_id, conn, limit=6),
        "accounts": await Account.fetch_all(user_id, conn),
        "menu_selection": "dashboard",
        "title": "Overview",
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    conn: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context=await _dashboard_context(user_id, conn)
    )


@router.get("/dashboard/partial", response_class=HTMLResponse)
async def dashboard_partial(
    request: Request,
    conn: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard/dashboard-partial.html",
        context=await _dashboard_context(user_id, conn),
    )


@router.get("/layout", response_class=HTMLResponse)
async def layout(
    request: Request,
):
    return RedirectResponse("/transactions", status_code=303)
