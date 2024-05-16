from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from asyncpg import Connection
from everwealth.db import get_connection
from fastapi.templating import Jinja2Templates
from everwealth import transactions
from everwealth.settings import categories
from everwealth.auth import auth_user

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/layout", response_class=HTMLResponse)
async def layout(request: Request, conn: Connection = Depends(get_connection), user_id: str = Depends(auth_user)):
    transactions_ = await transactions.fetch_many(user_id, conn)
    categories_ = await categories.fetch_many(user_id, conn)
    return templates.TemplateResponse(request=request, name="layout.html", context={"transactions": transactions_, "categories": categories_})

