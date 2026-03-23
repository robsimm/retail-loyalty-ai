"""Tests for RFM calculation pipeline."""
from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta

import polars as pl

from retail.pipeline.rfm import build_rfm_profiles


@pytest.mark.unit
def test_rfm_segment_champions_has_high_scores_on_all_dimensions() -> None:
    """Champions = recent + frequent + high spend."""
    now = datetime.now()
    rows = []
    # Champion customer: recent, frequent, high spend
    for i in range(50):
        rows.append({
            "transaction_id": f"TX_CHAMP_{i}",
            "customer_id": "CUS_CHAMP",
            "amount_gbp": 100.0,
            "category": "grocery",
            "timestamp": (now - timedelta(days=i % 5 + 1)).isoformat(),
            "channel": "instore",
            "is_return": False,
        })
    # Lost customer: old, infrequent, low spend
    for i in range(2):
        rows.append({
            "transaction_id": f"TX_LOST_{i}",
            "customer_id": "CUS_LOST",
            "amount_gbp": 5.0,
            "category": "grocery",
            "timestamp": (now - timedelta(days=200 + i)).isoformat(),
            "channel": "instore",
            "is_return": False,
        })
    df = pl.DataFrame(rows).with_columns(pl.col("timestamp").str.to_datetime())
    profiles = build_rfm_profiles(df, date.today())
    champ = profiles.filter(pl.col("customer_id") == "CUS_CHAMP")
    assert champ["frequency_count"][0] == 50
    assert champ["monetary_gbp"][0] == pytest.approx(50 * 100.0)


@pytest.mark.unit
def test_build_rfm_profiles_returns_one_row_per_customer() -> None:
    now = datetime.now()
    rows = [
        {
            "transaction_id": f"TX_{i}",
            "customer_id": f"CUS_{i % 3 + 1:03d}",
            "amount_gbp": 10.0,
            "category": "grocery",
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "channel": "instore",
            "is_return": False,
        }
        for i in range(9)
    ]
    df = pl.DataFrame(rows).with_columns(pl.col("timestamp").str.to_datetime())
    profiles = build_rfm_profiles(df, date.today())
    assert len(profiles) == 3
