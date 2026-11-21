"""Public marketing, help, and legal-information pages."""

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="everwealth/templates")


def _page(request: Request, template: str):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={"current_year": datetime.now().year},
    )


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return _page(request, "index.html")


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return _page(request, "marketing/about.html")


@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    return _page(request, "marketing/help.html")


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return _page(request, "marketing/legal/privacy.html")


@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return _page(request, "marketing/legal/terms.html")


@router.get("/cookies", response_class=HTMLResponse)
async def cookies(request: Request):
    return _page(request, "marketing/legal/cookies.html")
