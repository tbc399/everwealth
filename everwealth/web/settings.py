from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from everwealth.settings import create, fetch_many, default_category_names
from asyncpg import Connection
from everwealth.db import get_connection

from fastapi.responses import RedirectResponse
from fastapi import Depends
from everwealth.users import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/categories", response_class=HTMLResponse)
async def create_category(
    request: Request,
    name: Annotated[str, Form()],
    conn: Connection = Depends(get_connection),
):
    _ = await create(name, User(email="travis@email.com"), conn)
    return RedirectResponse(url="/categories", status_code=303)  # TODO: redirect to other page


@router.get("/categories", response_class=HTMLResponse)
async def get_categories(request: Request, conn: Connection = Depends(get_connection)):
    categories = await fetch_many(conn)
    # categories.extend(default_category_names)
    return templates.TemplateResponse(
        request=request,
        name="categories.html",
        context={"categories": categories},
    )
