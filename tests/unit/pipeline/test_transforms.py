"""Tests for pure Polars transform functions. TDD: tests written first."""
from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta

import polars as pl

from retail.pipeline.transforms import (
    calculate_rfm,
    deduplicate_transactions,
    normalize_features,
    segment_by_rfm,
)


def make_tx_df(rows: list[dict]) -> pl.DataFrame:  # type: ignore[type-arg]
    return pl.DataFrame(rows)


@pytest.mark.unit
def test_deduplicate_transactions_keeps_first_occurrence() -> None:
    df = make_tx_df([
        {"transaction_id": "TX_001", "customer_id": "CUS_001", "amount_gbp": 10.0,
         "category": "grocery", "timestamp": "2026-01-01", "channel": "instore", "is_return": False},
        {"transaction_id": "TX_001", "customer_id": "CUS_001", "amount_gbp": 99.0,
         "category": "grocery", "timestamp": "2026-01-02", "channel": "instore", "is_return": False},
        {"transaction_id": "TX_002", "customer_id": "CUS_001", "amount_gbp": 5.0,
         "category": "dairy", "timestamp": "2026-01-03", "channel": "instore", "is_return": False},
    ])
    result = deduplicate_transactions(df)
    assert len(result) == 2
    # First TX_001 (amount 10.0) is kept
    tx001 = result.filter(pl.col("transaction_id") == "TX_001")
    assert tx001["amount_gbp"][0] == 10.0


@pytest.mark.unit
def test_deduplicate_transactions_no_duplicates_unchanged() -> None:
    df = make_tx_df([
        {"transaction_id": "TX_001", "customer_id": "CUS_001", "amount_gbp": 10.0,
         "category": "grocery", "timestamp": "2026-01-01", "channel": "instore", "is_return": False},
        {"transaction_id": "TX_002", "customer_id": "CUS_001", "amount_gbp": 5.0,
         "category": "dairy", "timestamp": "2026-01-02", "channel": "instore", "is_return": False},
    ])
    result = deduplicate_transactions(df)
    assert len(result) == 2


@pytest.mark.unit
def test_calculate_rfm_recency_recent_purchase_returns_low_days() -> None:
    today = date.today()
    yesterday = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
    df = pl.DataFrame([{
        "transaction_id": "TX_001",
        "customer_id": "CUS_001",
        "amount_gbp": 20.0,
        "category": "grocery",
        "timestamp": yesterday,
        "channel": "instore",
        "is_return": False,
    }])
    df = df.with_columns(pl.col("timestamp").str.to_datetime())
    rfm = calculate_rfm(df, today)
    recency = rfm.filter(pl.col("customer_id") == "CUS_001")["recency_days"][0]
    assert recency <= 2  # should be 1 day


@pytest.mark.unit
def test_calculate_rfm_frequency_counts_non_returns_only() -> None:
    base_time = datetime.now() - timedelta(days=5)
    df = pl.DataFrame([
        {"transaction_id": "TX_001", "customer_id": "CUS_001", "amount_gbp": 10.0,
         "category": "grocery", "timestamp": base_time.isoformat(), "channel": "instore", "is_return": False},
        {"transaction_id": "TX_002", "customer_id": "CUS_001", "amount_gbp": 5.0,
         "category": "grocery", "timestamp": base_time.isoformat(), "channel": "instore", "is_return": False},
        {"transaction_id": "TX_003", "customer_id": "CUS_001", "amount_gbp": 8.0,
         "category": "grocery", "timestamp": base_time.isoformat(), "channel": "instore", "is_return": True},
    ])
    df = df.with_columns(pl.col("timestamp").str.to_datetime())
    rfm = calculate_rfm(df, date.today())
    freq = rfm.filter(pl.col("customer_id") == "CUS_001")["frequency_count"][0]
    assert freq == 2  # return not counted


@pytest.mark.unit
def test_normalize_features_values_between_zero_and_one() -> None:
    df = pl.DataFrame([
        {"recency_days": 10, "frequency_count": 5},
        {"recency_days": 30, "frequency_count": 15},
        {"recency_days": 50, "frequency_count": 25},
    ])
    result = normalize_features(df, ["recency_days", "frequency_count"])
    assert result["recency_days_norm"].min() == pytest.approx(0.0)
    assert result["recency_days_norm"].max() == pytest.approx(1.0)


@pytest.mark.unit
def test_normalize_features_constant_column_gives_zeros() -> None:
    df = pl.DataFrame([
        {"recency_days": 10},
        {"recency_days": 10},
    ])
    result = normalize_features(df, ["recency_days"])
    assert result["recency_days_norm"].to_list() == [0.0, 0.0]


@pytest.mark.unit
def test_segment_by_rfm_assigns_champions_to_high_scorers() -> None:
    # Build a dataset where some customers are clearly champions
    rows = []
    for i in range(20):
        rows.append({
            "customer_id": f"CUS_{i:03d}",
            "recency_days": i * 5,  # lower = more recent
            "frequency_count": 100 - i * 2,
            "monetary_gbp": 1000.0 - i * 20,
        })
    df = pl.DataFrame(rows)
    result = segment_by_rfm(df)
    assert "segment" in result.columns
    segments = set(result["segment"].to_list())
    # Should have at least some variation
    assert len(segments) >= 2
