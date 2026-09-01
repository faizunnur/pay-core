"""Fraud and risk scoring.

A payment is scored from 0 (looks fine) to 100 (looks bad). Anything at or
above RISK_ENGINE_THRESHOLD is declined by the payments router.

The score combines two things:

* static rules about the request itself (amount, currency, card token shape)
* the merchant's recent behaviour, which is cached in Redis and rebuilt from
  the transactions table when the cache does not have it
"""

import json
import logging
from dataclasses import dataclass, field

import redis
import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Transaction
from app.schemas import PaymentRequest

logger = logging.getLogger("paycore.risk_engine")

HISTORY_CACHE_TTL_SECONDS = 300
HIGH_VALUE_CENTS = 500_000
VERY_HIGH_VALUE_CENTS = 2_000_000
SUPPORTED_CURRENCIES = ("CAD", "USD", "EUR", "GBP")


@dataclass
class RiskDecision:
    """The outcome of scoring one payment."""

    score: int
    reasons: list[str] = field(default_factory=list)


@dataclass
class MerchantHistory:
    """A rolling summary of what a merchant has been doing."""

    transaction_count: int = 0
    declined_count: int = 0
    total_amount_cents: int = 0

    @property
    def decline_ratio(self) -> float:
        if self.transaction_count == 0:
            return 0.0
        return self.declined_count / self.transaction_count

    def as_dict(self) -> dict[str, int]:
        return {
            "transaction_count": self.transaction_count,
            "declined_count": self.declined_count,
            "total_amount_cents": self.total_amount_cents,
        }


def cache_client() -> redis.Redis | None:
    """Return a Redis client, or None when the cache is not reachable."""
    try:
        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        client.ping()
        return client
    except redis.RedisError as exc:
        logger.warning("cache unavailable, falling back to the database: %s", exc)
        return None


def history_cache_key(merchant_id: str) -> str:
    return f"paycore:merchant:{merchant_id}:history"


def load_merchant_history(db: Session, merchant_id: str) -> MerchantHistory:
    """Read the merchant summary from cache, rebuilding it from Postgres on a miss."""
    client = cache_client()

    if client is not None:
        cached = client.get(history_cache_key(merchant_id))
        if cached:
            return MerchantHistory(**json.loads(cached))

    history = rebuild_merchant_history(db, merchant_id)

    if client is not None:
        client.setex(
            history_cache_key(merchant_id),
            HISTORY_CACHE_TTL_SECONDS,
            json.dumps(history.as_dict()),
        )

    return history


def rebuild_merchant_history(db: Session, merchant_id: str) -> MerchantHistory:
    """Rebuild the merchant summary from the transactions table."""
    history = MerchantHistory()

    try:
        rows = db.query(Transaction).filter(Transaction.merchant_ref == merchant_id).all()
    except SQLAlchemyError as exc:
        logger.warning("could not read merchant history: %s", exc)
        return history

    for row in rows:
        history.transaction_count += 1
        history.total_amount_cents += row.amount_cents
        if row.status == "declined":
            history.declined_count += 1

    return history


def external_rules_verdict(payment: PaymentRequest) -> int:
    """Ask the shared rules service for extra points, when one is configured."""
    if not settings.rules_service_url:
        return 0

    try:
        response = requests.post(
            settings.rules_service_url,
            json={
                "merchant_id": payment.merchant_id,
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
            },
            timeout=settings.risk_engine_timeout_ms / 1000,
        )
        response.raise_for_status()
        return int(response.json().get("score", 0))
    except (requests.RequestException, ValueError) as exc:
        logger.warning("rules service call failed, scoring locally only: %s", exc)
        return 0


def score_payment(db: Session, payment: PaymentRequest) -> RiskDecision:
    """Score one payment request."""
    score = 0
    reasons: list[str] = []

    if payment.amount_cents >= VERY_HIGH_VALUE_CENTS:
        score += 60
        reasons.append("very_high_value")
    elif payment.amount_cents >= HIGH_VALUE_CENTS:
        score += 20
        reasons.append("high_value")

    if payment.currency.upper() not in SUPPORTED_CURRENCIES:
        score += 25
        reasons.append("unsupported_currency")

    if not payment.card_token.startswith("tok_"):
        score += 30
        reasons.append("unexpected_token_format")

    history = load_merchant_history(db, payment.merchant_id)

    if history.transaction_count == 0:
        score += 15
        reasons.append("first_transaction_for_merchant")
    elif history.decline_ratio > 0.3:
        score += 35
        reasons.append("merchant_decline_ratio_high")

    if history.transaction_count > 50 and payment.amount_cents >= HIGH_VALUE_CENTS:
        score += 10
        reasons.append("unusual_amount_for_merchant")

    score += external_rules_verdict(payment)

    return RiskDecision(score=min(score, 100), reasons=reasons)
