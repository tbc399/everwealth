from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.db import get_connection
from everwealth.settings import categories

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.post("/categories", response_class=HTMLResponse)
async def create_category(
    request: Request,
    name: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
):
    _ = await categories.create(name, request.user.id, db)
    return RedirectResponse(url="/categories", status_code=303)  # TODO: redirect to other page


@router.get("/categories", response_class=HTMLResponse)
async def get_categories(request: Request, db: Connection = Depends(get_connection)):
    cats = await categories.fetch_many(request.user.id, db)
    # categories.extend(default_category_names)
    return templates.TemplateResponse(
        request=request,
        name="categories.html",
        context={"categories": cats},
    )
