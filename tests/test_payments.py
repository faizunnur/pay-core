"""Tests for the payments endpoints."""

import uuid

import pytest


@pytest.fixture()
def payment_body():
    return {
        "merchant_id": str(uuid.uuid4()),
        "card_token": "tok_visa_4242",
        "amount_cents": 2500,
        "currency": "CAD",
        "description": "coffee beans",
    }


def test_small_payment_is_approved(client, payment_body):
    response = client.post("/payments", json=payment_body)

    assert response.status_code == 201
    receipt = response.json()
    assert receipt["status"] == "approved"
    assert receipt["amount_cents"] == 2500
    assert receipt["currency"] == "CAD"
    assert receipt["transaction_id"]


def test_very_large_payment_is_declined(client, payment_body):
    payment_body["amount_cents"] = 9_000_000

    receipt = client.post("/payments", json=payment_body).json()

    assert receipt["status"] == "declined"
    assert receipt["risk_score"] >= 70


def test_amount_must_be_positive(client, payment_body):
    payment_body["amount_cents"] = 0

    response = client.post("/payments", json=payment_body)

    assert response.status_code == 422


def test_currency_must_be_three_characters(client, payment_body):
    payment_body["currency"] = "CANADIAN"

    response = client.post("/payments", json=payment_body)

    assert response.status_code == 422


def test_receipt_can_be_fetched_again(client, payment_body):
    created = client.post("/payments", json=payment_body).json()

    response = client.get(f"/payments/{created['transaction_id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_unknown_transaction_returns_404(client):
    response = client.get(f"/payments/{uuid.uuid4()}")

    assert response.status_code == 404
