import asyncio
import os
import re
from contextlib import asynccontextmanager

import asyncpg

# import databases
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

# from loguru import logger as log
from starlette.middleware.cors import CORSMiddleware

from everwealth import db
from everwealth.config import settings
from everwealth.web.accounts import router as accounts_router

# from everwealth.config import lucy
# from everwealth.strategies import rebalance
# from everwealth.write.investment import api, event_store
# from everwealth.write.investment.tasks import snapshot
from everwealth.web.budget import router as budget_router
from everwealth.web.dashboard import router as dashboard_router
from everwealth.web.login import router as login_router
from everwealth.web.transactions import router as transaction_router


async def startup():
    setattr(db, "pool", await asyncpg.create_pool(settings.database_url))


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

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://makeshift-web-service.herokuapp.com",
        "https://makeshift-web-service.herokuapp.com",
        "http://localhost",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
