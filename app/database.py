"""Database engine and session management."""

import logging
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger("paycore.database")

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create the tables if they do not exist yet.

    Real deployments use migrations. This keeps the local stack a one-command
    start for the labs.
    """
    from app import models  # noqa: F401  (registers the models on Base)

    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        logger.warning("could not prepare the database schema: %s", exc)
