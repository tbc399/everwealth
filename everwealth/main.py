import asyncio

from fastapi.staticfiles import StaticFiles
import os
import re
from contextlib import asynccontextmanager

# import databases
from fastapi import APIRouter, FastAPI

# from loguru import logger as log
from starlette.middleware.cors import CORSMiddleware

# from everwealth.config import lucy
# from everwealth.strategies import rebalance
# from everwealth.write.investment import api, event_store
# from everwealth.write.investment.tasks import snapshot
from everwealth.web.budget import router as budget_router
from everwealth.web.login import router as login_router
from everwealth.web.transactions import router as transaction_router


async def startup():
    database_url = databases.DatabaseURL(
        re.sub("postgres:", "postgresql:", os.getenv("DATABASE_URL"))
    )
    setattr(
        database,
        "db",
        databases.Database(
            database_url,
            # ssl=create_default_context(capath=certifi.where()),
            ssl=False,
            min_size=1,
            max_size=3,
        ),
    )

    from .database import db

    await db.connect()

    log.info("Building aggregate state...")
    await event_store.build_state()

    log.info("Starting strategies")
    asyncio.create_task(rebalance.run())

    # TODO: start up lucette
    # asyncio.create_task(lucy.run())


async def shutdown():
    from .database import db

    await db.disconnect()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    asyncio.create_task(snapshot.run())
    yield
    await shutdown()


app = FastAPI()

app.mount("/static", StaticFiles(directory="everwealth/static"), name="static")
app.mount("/node_modules", StaticFiles(directory="node_modules"), name="modules")

api_router = APIRouter()
api_router.include_router(budget_router)
api_router.include_router(transaction_router)
api_router.include_router(login_router)

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
