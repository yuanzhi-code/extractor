import logging
from contextlib import asynccontextmanager

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.models import get_db_url
from src.workflows import fetch_task

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(
        {"default": SQLAlchemyJobStore(url=get_db_url())}
    )
    scheduler.add_job(
        # sample_task,
        fetch_task,
        "interval",
        hours=2,
        # seconds=10,
        # minutes=1,
        id="tagger task",
    )
    scheduler.start()
    logger.info(f"fastapi started")
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan, title="yuanzhi ai-extractor web API")


@app.get("/")
async def index():
    return "hello world"


async def sample_task():
    pass
