from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from asyncpg import Connection
from everwealth.db import get_connection
from fastapi.templating import Jinja2Templates
from everwealth.transactions import fetch_many

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/layout", response_class=HTMLResponse)
async def layout(request: Request, conn: Connection = Depends(get_connection)):
    transactions = await fetch_many(request.user, conn)
    return templates.TemplateResponse(request=request, name="layout.html", context={"transactions": transactions})

