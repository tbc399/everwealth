from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/index", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/logout", response_class=HTMLResponse)
def submit_login(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")


@router.get("/sorry", response_class=HTMLResponse)
def page_not_found(request: Request):
    return templates.TemplateResponse(request=request, name="404.html")
