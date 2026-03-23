from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from retail.recommendations.domain import Recommendation, RecommendationRequest

router = APIRouter(tags=["recommendations"])


class ProfileResponse(BaseModel):
    customer_id: str
    rfm_segment: str
    preferred_categories: list[str]


@router.get("/customers/{customer_id}/profile", response_model=ProfileResponse)
async def get_profile(customer_id: str, request: Request) -> ProfileResponse:
    """Get a customer's enriched profile."""
    profile = request.app.state.profiles_by_id.get(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return ProfileResponse(
        customer_id=customer_id,
        rfm_segment=profile.rfm_segment or "unknown",
        preferred_categories=profile.preferred_categories,
    )


@router.get("/customers/{customer_id}/recommendations", response_model=list[Recommendation])
async def get_recommendations(
    customer_id: str, request: Request, top_n: int = 10
) -> list[Recommendation]:
    """Get personalised recommendations for a customer."""
    if customer_id not in request.app.state.profiles_by_id:
        raise HTTPException(status_code=404, detail="Customer not found")
    req = RecommendationRequest(customer_id=customer_id, top_n=top_n)
    return request.app.state.engine.predict(req)
