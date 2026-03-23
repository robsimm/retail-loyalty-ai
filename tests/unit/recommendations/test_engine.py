"""Tests for KNN recommendation engine."""
from __future__ import annotations

import pytest

from retail.recommendations.domain import RecommendationRequest
from retail.recommendations.engine import KNNRecommendationEngine
from tests.conftest import make_catalogue, make_profile


def make_profiles(n: int = 10):  # type: ignore[return]
    cats = [["grocery", "dairy"], ["bakery", "produce"], ["meat", "frozen"]]
    return [
        make_profile(
            customer_id=f"CUS_{i:03d}",
            preferred_categories=cats[i % len(cats)],
            normalized_features=[float(i) / n, 1.0 - float(i) / n, 0.5],
        )
        for i in range(n)
    ]


@pytest.mark.unit
def test_knn_engine_init_with_empty_profiles_raises_value_error() -> None:
    engine = KNNRecommendationEngine(catalogue=make_catalogue())
    with pytest.raises(ValueError, match="empty profiles"):
        engine.fit([])


@pytest.mark.unit
def test_knn_engine_fit_returns_self_for_chaining() -> None:
    engine = KNNRecommendationEngine(catalogue=make_catalogue())
    result = engine.fit(make_profiles())
    assert result is engine


@pytest.mark.unit
def test_knn_engine_predict_returns_exactly_top_n_recommendations() -> None:
    catalogue = make_catalogue(n=20)
    engine = KNNRecommendationEngine(catalogue=catalogue)
    engine.fit(make_profiles(10))
    request = RecommendationRequest(customer_id="CUS_000", top_n=5)
    recs = engine.predict(request)
    assert len(recs) == 5


@pytest.mark.unit
def test_knn_engine_predict_raises_for_unknown_customer() -> None:
    engine = KNNRecommendationEngine(catalogue=make_catalogue())
    engine.fit(make_profiles(5))
    with pytest.raises(ValueError, match="Unknown customer_id"):
        engine.predict(RecommendationRequest(customer_id="UNKNOWN"))


@pytest.mark.unit
def test_knn_engine_predict_high_consideration_filter_returns_subset() -> None:
    catalogue = make_catalogue(n=20)  # every 5th product is high_consideration
    engine = KNNRecommendationEngine(catalogue=catalogue)
    engine.fit(make_profiles(10))
    request_all = RecommendationRequest(customer_id="CUS_000", top_n=10)
    request_hc = RecommendationRequest(
        customer_id="CUS_000", top_n=10, high_consideration_only=True
    )
    recs_all = engine.predict(request_all)
    recs_hc = engine.predict(request_hc)
    assert len(recs_hc) <= len(recs_all)


@pytest.mark.unit
def test_knn_engine_predict_batch_processes_multiple_requests() -> None:
    catalogue = make_catalogue(n=20)
    engine = KNNRecommendationEngine(catalogue=catalogue)
    engine.fit(make_profiles(10))
    requests = [
        RecommendationRequest(customer_id="CUS_000", top_n=3),
        RecommendationRequest(customer_id="CUS_001", top_n=3),
    ]
    results = engine.predict_batch(requests)
    assert len(results) == 2
    assert all(len(r) == 3 for r in results)
