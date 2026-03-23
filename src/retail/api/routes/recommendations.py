from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from retail.recommendations.domain import Recommendation

router = APIRouter(tags=["recommendations"])


class ProfileResponse(BaseModel):
    customer_id: str
    rfm_segment: str
    preferred_categories: list[str]


@router.get("/customers/{customer_id}/profile", response_model=ProfileResponse)
async def get_profile(customer_id: str) -> ProfileResponse:
    """Get a customer's enriched profile."""
    # Stub: load from DB in production
    return ProfileResponse(
        customer_id=customer_id,
        rfm_segment="at_risk",
        preferred_categories=["grocery", "dairy"],
    )


@router.get("/customers/{customer_id}/recommendations", response_model=list[Recommendation])
async def get_recommendations(customer_id: str, top_n: int = 10) -> list[Recommendation]:
    """Get personalised recommendations for a customer."""
    # Stub: load KNN engine and predict in production
    return []
