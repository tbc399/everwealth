from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.models import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login", response_class=HTMLResponse)
async def submit_login(request: Request, email: Annotated[str, Form()]):
    # TODO: perfomr login auth
    return RedirectResponse(url="/transactions", status_code=303)
