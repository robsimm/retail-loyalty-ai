from __future__ import annotations

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """A personalised product recommendation for a customer."""

    product_id: str
    product_name: str
    category: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    reason: str = ""
    rank: int = Field(ge=1)

    model_config = {"frozen": True}


class RecommendationRequest(BaseModel):
    """Request for personalised recommendations."""

    customer_id: str
    k_neighbors: int = Field(default=30, ge=1)
    top_n: int = Field(default=10, ge=1)
    high_consideration_only: bool = False
