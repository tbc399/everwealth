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
        Budget(category="Groceries", amount=40, spent=40),
        Budget(category="Gas", amount=23, spent=11),
        Budget(category="Home School", amount=100, spent=98),
        Budget(category="Entertainment", amount=55, spent=50),
        Budget(category="Date Night", amount=100, spent=10),
        Budget(category="Water", amount=75, spent=45),
        Budget(category="Pet", amount=90, spent=23),
        Budget(category="Tiingo", amount=10, spent=5),
    ]
    return templates.TemplateResponse(
        request=request,
        name="budgets.html",
        context={"budgets": budgets},
    )


@router.get("/budgets-v2", response_class=HTMLResponse)
async def budgets_v2(request: Request):
    budgets = [
        Budget(category="Groceries", amount=40, spent=40),
        Budget(category="Gas", amount=23, spent=11),
        Budget(category="Home School", amount=100, spent=98),
        Budget(category="Entertainment", amount=55, spent=50),
        Budget(category="Date Night", amount=100, spent=10),
        Budget(category="Water", amount=75, spent=45),
        Budget(category="Pet", amount=90, spent=23),
        Budget(category="Tiingo", amount=10, spent=5),
    ]
    return templates.TemplateResponse(
        request=request,
        name="budgets2.html",
        context={"budgets": budgets},
    )


@router.get("/budget_section", response_class=HTMLResponse)
async def budget_section(request: Request):
    return templates.TemplateResponse(request=request, name="partials/budget.html")
