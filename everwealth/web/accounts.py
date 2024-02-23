from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/accounts", response_class=HTMLResponse)
async def get_accounts(request: Request):
    return templates.TemplateResponse(request=request, name="accounts.html")

