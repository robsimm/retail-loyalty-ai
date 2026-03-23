from __future__ import annotations

from typing import Self

import numpy as np
from sklearn.neighbors import NearestNeighbors

from retail.domain.customer import ShopperProfile
from retail.domain.product import Catalogue, Product
from retail.recommendations.domain import Recommendation, RecommendationRequest
from retail.recommendations.features import feature_vector_from_profile


class KNNRecommendationEngine:
    """
    KNN-based personalised recommendation engine.

    Usage:
        engine = KNNRecommendationEngine(catalogue)
        engine.fit(profiles)
        recs = engine.predict(RecommendationRequest(customer_id="CUS_001", top_n=5))
    """

    def __init__(self, catalogue: Catalogue) -> None:
        self._catalogue = catalogue
        self._profiles: list[ShopperProfile] = []
        self._feature_matrix: np.ndarray | None = None
        self._nn: NearestNeighbors | None = None

    def fit(self, profiles: list[ShopperProfile]) -> Self:
        if not profiles:
            raise ValueError("Cannot fit KNN engine with empty profiles list")

        self._profiles = profiles
        vectors = np.array([feature_vector_from_profile(p) for p in profiles], dtype=np.float64)

        # Normalise rows to unit length for cosine distance via Euclidean
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._feature_matrix = vectors / norms

        n_neighbors = min(len(profiles), 30)
        self._nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean", algorithm="auto")
        self._nn.fit(self._feature_matrix)
        return self

    def predict(self, request: RecommendationRequest) -> list[Recommendation]:
        if self._nn is None or self._feature_matrix is None:
            raise RuntimeError("Engine not fitted. Call .fit() first.")

        profile = next((p for p in self._profiles if p.customer_id == request.customer_id), None)
        if profile is None:
            raise ValueError(f"Unknown customer_id: {request.customer_id}")

        query = feature_vector_from_profile(profile).reshape(1, -1)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        k = min(request.k_neighbors, len(self._profiles))
        distances, indices = self._nn.kneighbors(query, n_neighbors=k)

        # Collect candidate products from similar customers' preferred categories
        neighbour_categories: list[str] = []
        for idx in indices[0]:
            neighbour_categories.extend(self._profiles[idx].preferred_categories)

        # Rank catalogue products by how often they appear in neighbour categories
        category_counts: dict[str, int] = {}
        for cat in neighbour_categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        candidates: list[Product] = self._catalogue.products
        if request.high_consideration_only:
            candidates = [p for p in candidates if p.is_high_consideration]

        # Score products by category affinity
        def product_score(p: Product) -> float:
            return float(category_counts.get(p.category, 0))

        ranked = sorted(candidates, key=product_score, reverse=True)

        recommendations: list[Recommendation] = []
        for i, product in enumerate(ranked[: request.top_n], start=1):
            score = product_score(product) / max(len(neighbour_categories), 1)
            recommendations.append(
                Recommendation(
                    product_id=product.product_id,
                    product_name=product.name,
                    category=product.category,
                    similarity_score=min(score, 1.0),
                    reason=f"Popular in your preferred categories (k={k} neighbours)",
                    rank=i,
                )
            )
        return recommendations

    def predict_batch(
        self, requests: list[RecommendationRequest]
    ) -> list[list[Recommendation]]:
        return [self.predict(r) for r in requests]
