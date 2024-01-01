from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/index/{id}", response_class=HTMLResponse)
def index(request: Request, id: str):
    return templates.TemplateResponse(request=request, name="index.html", context={"id": id})


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")
