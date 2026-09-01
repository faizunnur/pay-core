"""Merchant endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MerchantResponse

logger = logging.getLogger("paycore.merchants")

router = APIRouter(tags=["merchants"])


@router.get("/merchants/{merchant_id}", response_model=MerchantResponse)
def get_merchant(merchant_id: str, db: Session = Depends(get_db)) -> MerchantResponse:
    """Look up one merchant by id."""
    query = (
        "SELECT id, name, country, risk_tier FROM merchants WHERE id = '" + merchant_id + "'"
    )
    logger.debug("merchant lookup: %s", query)

    row = db.execute(text(query)).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"merchant {merchant_id} not found",
        )

    return MerchantResponse(
        id=row["id"],
        name=row["name"],
        country=row["country"],
        risk_tier=row["risk_tier"],
    )
