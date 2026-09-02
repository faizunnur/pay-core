"""Tests for the risk engine."""

import uuid

import pytest

from app.models import Transaction
from app.schemas import PaymentRequest
from services.risk_engine import (
    MerchantHistory,
    rebuild_merchant_history,
    score_payment,
)


def make_payment(**overrides) -> PaymentRequest:
    body = {
        "merchant_id": str(uuid.uuid4()),
        "card_token": "tok_visa_4242",
        "amount_cents": 1000,
        "currency": "CAD",
    }
    body.update(overrides)
    return PaymentRequest(**body)


@pytest.fixture()
def merchant_with_history(db_session):
    merchant_id = str(uuid.uuid4())
    rows = [
        Transaction(
            id=str(uuid.uuid4()),
            merchant_ref=merchant_id,
            card_token="tok_visa_1111",
            amount_cents=1000,
            currency="CAD",
            status="approved" if index % 4 else "declined",
            risk_score=10,
        )
        for index in range(8)
    ]
    db_session.add_all(rows)
    db_session.commit()
    return merchant_id


def test_a_known_merchant_scores_lower_than_a_new_one(db_session, merchant_with_history):
    new_merchant = score_payment(db_session, make_payment())
    known_merchant = score_payment(db_session, make_payment(merchant_id=merchant_with_history))

    assert "first_transaction_for_merchant" in new_merchant.reasons
    assert known_merchant.score < new_merchant.score


def test_very_high_value_is_flagged(db_session):
    decision = score_payment(db_session, make_payment(amount_cents=3_000_000))

    assert "very_high_value" in decision.reasons
    assert decision.score >= 60


def test_unsupported_currency_is_flagged(db_session):
    decision = score_payment(db_session, make_payment(currency="XYZ"))

    assert "unsupported_currency" in decision.reasons


def test_unexpected_token_format_is_flagged(db_session):
    decision = score_payment(db_session, make_payment(card_token="4242424242424242"))

    assert "unexpected_token_format" in decision.reasons


def test_score_never_exceeds_100(db_session):
    decision = score_payment(
        db_session,
        make_payment(amount_cents=9_000_000, currency="XYZ", card_token="4242424242424242"),
    )

    assert decision.score == 100


def test_history_is_rebuilt_from_the_database(db_session, merchant_with_history):
    history = rebuild_merchant_history(db_session, merchant_with_history)

    assert history.transaction_count == 8
    assert history.declined_count == 2
    assert history.total_amount_cents == 8000


def test_decline_ratio_of_an_unseen_merchant_is_zero():
    assert MerchantHistory().decline_ratio == 0.0
