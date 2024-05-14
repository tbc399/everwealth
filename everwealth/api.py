from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from everwealth.models import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/index", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/base", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    print(request)
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/submit_login", response_class=HTMLResponse)
async def submit_login(
    request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()]
):
    print(username)
    print(password)
    return templates.TemplateResponse(request=request, name="home.html")


@router.get("/sorry", response_class=HTMLResponse)
def page_not_found(request: Request):
    return templates.TemplateResponse(request=request, name="404.html")
