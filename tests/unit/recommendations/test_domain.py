"""Tests for recommendation domain models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from retail.recommendations.domain import Recommendation, RecommendationRequest


@pytest.mark.unit
def test_recommendation_creation_with_valid_data() -> None:
    rec = Recommendation(
        product_id="PRD_001",
        product_name="Organic Milk",
        category="dairy",
        similarity_score=0.85,
        reason="Popular in your categories",
        rank=1,
    )
    assert rec.rank == 1
    assert rec.similarity_score == pytest.approx(0.85)


@pytest.mark.unit
def test_recommendation_similarity_score_must_be_between_0_and_1() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            product_id="PRD_001",
            product_name="Milk",
            category="dairy",
            similarity_score=1.5,
            rank=1,
        )


@pytest.mark.unit
def test_recommendation_request_defaults() -> None:
    req = RecommendationRequest(customer_id="CUS_001")
    assert req.k_neighbors == 30
    assert req.top_n == 10
    assert req.high_consideration_only is False
