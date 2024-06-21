from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from everwealth.db import get_connection
from everwealth.settings import categories
from everwealth.auth import auth_user

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")
