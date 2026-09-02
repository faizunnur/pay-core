"""Liveness and readiness endpoints."""

import logging

import redis
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import __version__
from app.config import settings
from app.database import get_db
from app.schemas import HealthResponse, ReadyResponse

logger = logging.getLogger("paycore.health")

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness: the process is up and serving requests."""
    return HealthResponse(
        status="ok",
        service="paycore",
        version=__version__,
        environment=settings.app_env,
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(response: Response, db: Session = Depends(get_db)) -> ReadyResponse:
    """Readiness: the dependencies this service needs are reachable."""
    database_state = "ok"
    cache_state = "ok"

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("database readiness check failed: %s", exc)
        database_state = "unavailable"

    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
        client.ping()
    except redis.RedisError as exc:
        logger.warning("cache readiness check failed: %s", exc)
        cache_state = "unavailable"

    ready_now = database_state == "ok" and cache_state == "ok"
    if not ready_now:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(
        status="ready" if ready_now else "not_ready",
        database=database_state,
        cache=cache_state,
    )
