"""Payment endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Transaction
from app.schemas import PaymentReceipt, PaymentRequest
from services.ledger import record_transaction
from services.risk_engine import score_payment

logger = logging.getLogger("paycore.payments")

router = APIRouter(tags=["payments"])


@router.post("/payments", response_model=PaymentReceipt, status_code=status.HTTP_201_CREATED)
def create_payment(payment: PaymentRequest, db: Session = Depends(get_db)) -> PaymentReceipt:
    """Take a payment request, risk-check it, and write it to the ledger."""
    logger.info("POST /payments received: %s", payment.model_dump())

    decision = score_payment(db, payment)
    outcome = "declined" if decision.score >= settings.risk_engine_threshold else "approved"

    transaction = record_transaction(db, payment, outcome, decision.score)

    logger.info(
        "payment %s for merchant %s: %s (score=%s, reasons=%s)",
        transaction.id,
        payment.merchant_id,
        outcome,
        decision.score,
        ",".join(decision.reasons) or "none",
    )

    return PaymentReceipt(
        transaction_id=transaction.id,
        merchant_id=transaction.merchant_ref,
        amount_cents=transaction.amount_cents,
        currency=transaction.currency,
        status=transaction.status,
        risk_score=transaction.risk_score,
        created_at=transaction.created_at,
    )


@router.get("/payments/{transaction_id}", response_model=PaymentReceipt)
def get_payment(transaction_id: str, db: Session = Depends(get_db)) -> PaymentReceipt:
    """Fetch a single receipt by transaction id."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"transaction {transaction_id} not found",
        )

    return PaymentReceipt(
        transaction_id=transaction.id,
        merchant_id=transaction.merchant_ref,
        amount_cents=transaction.amount_cents,
        currency=transaction.currency,
        status=transaction.status,
        risk_score=transaction.risk_score,
        created_at=transaction.created_at,
    )
