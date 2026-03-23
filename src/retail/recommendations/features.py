from __future__ import annotations

import numpy as np

from retail.domain.customer import ShopperProfile

CATEGORY_VOCAB = [
    "grocery",
    "dairy",
    "bakery",
    "produce",
    "meat",
    "frozen",
    "beverages",
    "snacks",
    "household",
    "personal_care",
]


def category_one_hot(categories: list[str]) -> list[float]:
    """Encode preferred categories as a one-hot vector over CATEGORY_VOCAB."""
    vec = [0.0] * len(CATEGORY_VOCAB)
    for cat in categories:
        cat_lower = cat.lower()
        if cat_lower in CATEGORY_VOCAB:
            vec[CATEGORY_VOCAB.index(cat_lower)] = 1.0
    return vec


def channel_to_float(channel: str) -> float:
    mapping = {"online": 0.0, "both": 0.5, "instore": 1.0}
    return mapping.get(channel, 0.5)


def feature_vector_from_profile(profile: ShopperProfile) -> np.ndarray:  # type: ignore[type-arg]
    """
    Build a numeric feature vector for KNN distance calculation.

    Vector layout (13 dims):
    [recency_norm, frequency_norm, monetary_norm,
     channel_preference_float,
     category_one_hot x10]
    """
    rfm = profile.normalized_features[:3] if len(profile.normalized_features) >= 3 else [0.0, 0.0, 0.0]
    channel = channel_to_float(profile.channel_preference)
    cats = category_one_hot(profile.preferred_categories)
    return np.array(rfm + [channel] + cats, dtype=np.float64)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:  # type: ignore[type-arg]
    """Cosine similarity between two vectors. Returns value in [0, 1]."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
