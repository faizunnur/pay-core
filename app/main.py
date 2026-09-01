"""PayCore FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.config import settings
from app.database import init_db
from app.routers import health, merchants, payments

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("paycore")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare the schema on startup so the local stack is a one-command start."""
    logger.info("starting paycore %s in %s", __version__, settings.app_env)
    init_db()
    yield
    logger.info("paycore shutting down")


app = FastAPI(
    title="PayCore Payments API",
    description="Internal payments API for Northwind Retail.",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(payments.router)
app.include_router(merchants.router)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    """Point callers at the generated API docs."""
    return {"service": "paycore", "version": __version__, "docs": "/docs"}
