"""Shared test fixtures.

Tests run against an in-memory SQLite database and with the cache switched off,
so `pytest` works on a laptop with nothing else running.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from services import risk_engine


@pytest.fixture()
def db_session():
    """A throwaway database session backed by SQLite."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(autouse=True)
def no_cache(monkeypatch):
    """Score every payment against the database, never a warm cache."""
    monkeypatch.setattr(risk_engine, "cache_client", lambda: None)


@pytest.fixture()
def client(db_session):
    """A test client wired to the throwaway database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
