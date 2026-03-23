"""Tests for feature engineering functions."""
from __future__ import annotations

import pytest
import numpy as np

from retail.recommendations.features import (
    category_one_hot,
    channel_to_float,
    cosine_similarity,
    feature_vector_from_profile,
    CATEGORY_VOCAB,
)
from tests.conftest import make_profile


@pytest.mark.unit
def test_feature_vector_from_profile_has_correct_dimensionality() -> None:
    profile = make_profile()
    vec = feature_vector_from_profile(profile)
    # 3 RFM + 1 channel + 10 category = 14
    assert vec.shape == (14,)


@pytest.mark.unit
def test_category_one_hot_known_category_sets_correct_bit() -> None:
    vec = category_one_hot(["grocery"])
    idx = CATEGORY_VOCAB.index("grocery")
    assert vec[idx] == 1.0
    assert sum(vec) == 1.0


@pytest.mark.unit
def test_category_one_hot_unknown_category_returns_zeros() -> None:
    vec = category_one_hot(["xyz_unknown"])
    assert sum(vec) == 0.0


@pytest.mark.unit
def test_channel_to_float_known_values() -> None:
    assert channel_to_float("online") == 0.0
    assert channel_to_float("instore") == 1.0
    assert channel_to_float("both") == 0.5


@pytest.mark.unit
def test_cosine_similarity_identical_vectors_returns_one() -> None:
    v = np.array([1.0, 2.0, 3.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0)


@pytest.mark.unit
def test_cosine_similarity_orthogonal_vectors_returns_zero() -> None:
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert cosine_similarity(a, b) == pytest.approx(0.0)


@pytest.mark.unit
def test_cosine_similarity_zero_vector_returns_zero() -> None:
    a = np.array([0.0, 0.0, 0.0])
    b = np.array([1.0, 2.0, 3.0])
    assert cosine_similarity(a, b) == 0.0
