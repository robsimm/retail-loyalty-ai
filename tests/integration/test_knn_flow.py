"""Integration tests: profiles → recommendations."""
from __future__ import annotations

import pytest

from retail.recommendations.domain import RecommendationRequest
from retail.recommendations.engine import KNNRecommendationEngine
from tests.conftest import make_catalogue, make_profile


@pytest.mark.integration
def test_knn_flow_fit_and_predict_full_cycle() -> None:
    profiles = [
        make_profile(
            customer_id=f"CUS_{i:03d}",
            preferred_categories=["grocery", "dairy"] if i % 2 == 0 else ["bakery", "produce"],
            normalized_features=[float(i) / 20, 1.0 - float(i) / 20, 0.5],
        )
        for i in range(20)
    ]
    catalogue = make_catalogue(n=30)
    engine = KNNRecommendationEngine(catalogue=catalogue)
    engine.fit(profiles)

    request = RecommendationRequest(customer_id="CUS_000", top_n=5)
    recs = engine.predict(request)

    assert len(recs) == 5
    assert all(r.rank > 0 for r in recs)
    assert all(0.0 <= r.similarity_score <= 1.0 for r in recs)


@pytest.mark.integration
def test_knn_flow_batch_prediction_matches_individual() -> None:
    profiles = [
        make_profile(
            customer_id=f"CUS_{i:03d}",
            normalized_features=[float(i) / 10, 0.5, 0.5],
        )
        for i in range(10)
    ]
    catalogue = make_catalogue(n=20)
    engine = KNNRecommendationEngine(catalogue=catalogue)
    engine.fit(profiles)

    requests = [
        RecommendationRequest(customer_id="CUS_000", top_n=3),
        RecommendationRequest(customer_id="CUS_001", top_n=3),
    ]
    batch_results = engine.predict_batch(requests)
    individual_0 = engine.predict(requests[0])
    individual_1 = engine.predict(requests[1])

    assert [r.product_id for r in batch_results[0]] == [r.product_id for r in individual_0]
    assert [r.product_id for r in batch_results[1]] == [r.product_id for r in individual_1]
