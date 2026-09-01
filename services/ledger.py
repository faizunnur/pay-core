"""Writes the transaction record."""

import logging
import uuid

from sqlalchemy.orm import Session

from app.models import Transaction
from app.schemas import PaymentRequest

logger = logging.getLogger("paycore.ledger")


def record_transaction(
    db: Session,
    payment: PaymentRequest,
    status: str,
    risk_score: int,
) -> Transaction:
    """Persist one payment attempt and return the stored row."""
    transaction = Transaction(
        id=str(uuid.uuid4()),
        merchant_ref=payment.merchant_id,
        card_token=payment.card_token,
        amount_cents=payment.amount_cents,
        currency=payment.currency.upper(),
        status=status,
        risk_score=risk_score,
        description=payment.description,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info("ledger wrote transaction %s with status %s", transaction.id, status)
    return transaction
