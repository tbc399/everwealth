from fastapi import APIRouter, Request, Form
from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from everwealth.models import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/create_budget", response_class=HTMLResponse)
async def create_budget(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/budgets", response_class=HTMLResponse)
async def budgets(request: Request):
    return templates.TemplateResponse(request=request, name="budgets.html")
