"""Pydantic request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequest(BaseModel):
    """Body of POST /payments."""

    merchant_id: str = Field(min_length=1, max_length=36)
    card_token: str = Field(min_length=8, max_length=64)
    amount_cents: int = Field(gt=0, le=100_000_000)
    currency: str = Field(min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=255)


class PaymentReceipt(BaseModel):
    """What the caller gets back after a payment attempt."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    merchant_id: str
    amount_cents: int
    currency: str
    status: str
    risk_score: int
    created_at: datetime


class MerchantResponse(BaseModel):
    """Body of GET /merchants/{id}."""

    id: str
    name: str
    country: str
    risk_tier: str


class HealthResponse(BaseModel):
    """Body of GET /health."""

    status: str
    service: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    """Body of GET /ready."""

    status: str
    database: str
    cache: str
