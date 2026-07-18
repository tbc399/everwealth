from datetime import datetime
from typing import Annotated, Optional

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.auth import auth_user
from everwealth.db import get_connection

router = APIRouter()
templates = Jinja2Templates(directory="everwealth/templates")


async def _profile(user_id: str, db: Connection) -> dict:
    record = await db.fetchrow(
        """
        SELECT u.email, p.first, p.last
        FROM users u LEFT JOIN profiles p ON p.user_id = u.id
        WHERE u.id = $1
        """,
        user_id,
    )
    return dict(record) if record else {"email": "", "first": "", "last": ""}


@router.get("/settings", response_class=HTMLResponse)
@router.get("/settings/profile", response_class=HTMLResponse)
async def get_settings(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        "settings/profile.html",
        {
            "request": request,
            "profile": await _profile(user_id, db),
            "menu_selection": "settings",
            "title": "Profile",
        },
    )


@router.get("/settings/partial", response_class=HTMLResponse)
async def get_settings_partial(
    request: Request,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    return templates.TemplateResponse(
        "settings/profile-partial.html",
        {"request": request, "profile": await _profile(user_id, db)},
    )


@router.post("/settings/profile")
async def update_profile(
    first: Annotated[Optional[str], Form()] = None,
    last: Annotated[Optional[str], Form()] = None,
    db: Connection = Depends(get_connection),
    user_id: str = Depends(auth_user),
):
    now = datetime.utcnow()
    await db.execute(
        """
        INSERT INTO profiles (id, user_id, first, last, created_at, updated_at)
        VALUES (substr(md5(random()::text), 1, 22), $1, $2, $3, $4, $4)
        ON CONFLICT (user_id) DO UPDATE SET
            first = EXCLUDED.first, last = EXCLUDED.last, updated_at = EXCLUDED.updated_at
        """,
        user_id,
        first,
        last,
        now,
    )
    return RedirectResponse("/settings/profile", status_code=303)
