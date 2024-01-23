from fastapi import APIRouter, Request, Form
from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from everwealth.models import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/transactions", response_class=HTMLResponse)
async def get_transactions(request: Request):
    return templates.TemplateResponse(request=request, name="transactions.html")


