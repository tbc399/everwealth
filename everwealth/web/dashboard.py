from asyncpg import Connection
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from everwealth import transactions
from everwealth.auth import auth_user
from everwealth.budgets import Category
from everwealth.db import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/dashboard/partial", response_class=HTMLResponse)
async def dashboard_partial(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard/dashboard-partial.html")


@router.get("/layout", response_class=HTMLResponse)
async def layout(
    request: Request, conn: Connection = Depends(get_connection), user_id: str = Depends(auth_user)
):
    transactions_ = await transactions.fetch_many(user_id, conn)
    categories_ = await Category.fetch_many(user_id, conn)
    return templates.TemplateResponse(
        request=request,
        name="layout.html",
        context={"transactions": transactions_, "categories": categories_},
    )
