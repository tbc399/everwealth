import asyncio
import os
import re
from contextlib import asynccontextmanager

import databases
from fastapi import APIRouter, FastAPI
from loguru import logger as log
from starlette.middleware.cors import CORSMiddleware

from makeshift.config import lucy
from makeshift.strategies import rebalance
from makeshift.write.investment import api, event_store
from makeshift.write.investment.tasks import snapshot

from . import database


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


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# app.include_router(investment.router)
# api_router.include_router(view.router)
api_router.include_router(api.router)

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
