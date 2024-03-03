from fastapi import APIRouter, Request, Form
from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from everwealth.models import User, Budget

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/create_budget", response_class=HTMLResponse)
async def create_budget(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/budgets", response_class=HTMLResponse)
async def budgets(request: Request):
    budgets = [
        Budget(category="Groceries", amount=40, percentage=50),
        Budget(category="Gas", amount=23, percentage=50),
        Budget(category="Home School", amount=100, percentage=50),
        Budget(category="Entertainment", amount=55, percentage=50),
        Budget(category="Date Night", amount=100, percentage=50),
        Budget(category="Water", amount=75, percentage=50),
        Budget(category="Pet", amount=90, percentage=50),
        Budget(category="Tiingo", amount=10, percentage=50),
    ]
    return templates.TemplateResponse(
        request=request,
        name="budgets.html",
        context={"budgets": budgets},
    )


@router.get("/budget_section", response_class=HTMLResponse)
async def budget_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/budget.html")
