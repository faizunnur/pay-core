"""SQLAlchemy models for PayCore."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Merchant(Base):
    """A shop that is allowed to take payments through PayCore."""

    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, default=_new_id)
    name = Column(String(120), nullable=False)
    country = Column(String(2), nullable=False, default="CA")
    risk_tier = Column(String(16), nullable=False, default="standard")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    def __repr__(self) -> str:
        return f"<Merchant {self.id} {self.name}>"


class Transaction(Base):
    """One attempted payment and what PayCore decided about it."""

    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=_new_id)
    merchant_ref = Column(String(36), nullable=False)
    card_token = Column(String(64), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(16), nullable=False)
    risk_score = Column(Integer, nullable=False, default=0)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    def __repr__(self) -> str:
        return f"<Transaction {self.id} {self.status} {self.amount_cents}>"
