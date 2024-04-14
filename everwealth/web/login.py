from typing import Annotated
from asyncpg import Connection
from asyncpg import Connection

from fastapi import APIRouter, Form, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.db import get_connection
from everwealth.users import fetch_user, create_user

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login", response_class=HTMLResponse)
async def submit_login(
    request: Request, email: Annotated[str, Form()], conn: Connection = Depends(get_connection)
):
    # TODO add handling for email validation
    # TODO handle a redirect page if it comes in
    user = await fetch_user(email, conn)
    if user:
        print(f"user {email} already exists in db")
    else:
        await create_user(email, conn)
        print(f"Created user {email}")

    return RedirectResponse(url="/dashboard", status_code=303)  # TODO: redirect to other page


@router.get("/not-found", response_class=HTMLResponse)
def page_not_found(request: Request):
    return templates.TemplateResponse(request=request, name="404.html")
