import asyncio
import inspect
import logging
from contextlib import asynccontextmanager

import asyncpg
import lucette

# import databases
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.exceptions import HTTPException as StartletteHTTPException

# from loguru import logger as log
from starlette.middleware.cors import CORSMiddleware

from everwealth import db

# from everwealth.auth.middleware import SessionBackend
from everwealth.auth.web import router as login_router

# from everwealth.config import lucy
# from everwealth.strategies import rebalance
# from everwealth.write.investment import api, event_store
# from everwealth.write.investment.tasks import snapshot
from everwealth.budgets.web import router as budget_router
from everwealth.config import settings
from everwealth.settings.categories.web import router as settings_router
from everwealth.transactions.web import router as transaction_router
from everwealth.web.accounts import router as accounts_router
from everwealth.web.dashboard import router as dashboard_router
from everwealth.lucy_config import lucy

templates = Jinja2Templates(directory="everwealth/templates")


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


async def startup():
    setattr(db, "pool", await asyncpg.create_pool(settings.database_url))
    asyncio.create_task(lucy.run())


async def shutdown():
    from everwealth import db

    await db.pool.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="everwealth/static"), name="static")
app.mount("/node_modules", StaticFiles(directory="node_modules"), name="modules")

api_router = APIRouter()
api_router.include_router(budget_router)
api_router.include_router(transaction_router)
api_router.include_router(login_router)
api_router.include_router(dashboard_router)
api_router.include_router(accounts_router)
api_router.include_router(settings_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://makeshift-web-service.herokuapp.com",
        # "https://makeshift-web-service.herokuapp.com",
        "http://localhost",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StartletteHTTPException)
async def exception_handler(request: Request, exc):
    if exc.status_code == 401:
        if "HX-Request" in request.headers:
            return Response(status_code=200, headers={"HX-Redirect": "/login"})
        else:
            return RedirectResponse(url="/login", status_code=303)
    return http_exception_handler(request, exc)


# app.add_middleware(AuthenticationMiddleware, backend=SessionBackend())
