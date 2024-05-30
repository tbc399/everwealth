from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.db import get_connection
from everwealth.settings import create, default_category_names, fetch_many
from everwealth.users import User

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/settings", response_class=HTMLResponse)
async def create_category(
    request: Request,
    name: Annotated[str, Form()],
    conn: Connection = Depends(get_connection),
):
    _ = await create(name, User(email="travis@email.com"), conn)
    return RedirectResponse(url="/categories", status_code=303)  # TODO: redirect to other page


@router.get("/settings", response_class=HTMLResponse)
async def get_categories(request: Request, db: Connection = Depends(get_connection)):
    categories = await fetch_many(None, db)
    # categories.extend(default_category_names)
    return templates.TemplateResponse(
        request=request,
        name="categories.html",
        context={"categories": categories},
    )
