"""Integration tests: CSV / DataFrame → RFM profiles end-to-end."""
from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta

import polars as pl

from retail.pipeline.pipeline import TransactionPipeline


@pytest.mark.integration
def test_pipeline_flow_produces_profiles_for_all_customers() -> None:
    now = datetime.now()
    rows = []
    for cust_i in range(10):
        for tx_i in range(5):
            rows.append({
                "transaction_id": f"TX_{cust_i}_{tx_i}",
                "customer_id": f"CUS_{cust_i + 1:03d}",
                "amount_gbp": 20.0 + tx_i,
                "category": "grocery",
                "timestamp": (now - timedelta(days=tx_i + 1)).isoformat(),
                "channel": "instore",
                "is_return": False,
            })

    df = pl.DataFrame(rows).with_columns(pl.col("timestamp").str.to_datetime())

    profiles = (
        TransactionPipeline()
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm(as_of_date=date.today())
        .to_profiles()
    )

    assert len(profiles) == 10
    for p in profiles:
        assert p.rfm_segment in ("champions", "loyal", "at_risk", "lost")
        assert len(p.normalized_features) == 3


@pytest.mark.integration
def test_pipeline_flow_deduplicates_duplicate_transactions() -> None:
    now = datetime.now()
    rows = [
        {
            "transaction_id": "TX_DUP",
            "customer_id": "CUS_001",
            "amount_gbp": 10.0,
            "category": "grocery",
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "channel": "instore",
            "is_return": False,
        },
        {
            "transaction_id": "TX_DUP",  # duplicate
            "customer_id": "CUS_001",
            "amount_gbp": 999.0,
            "category": "grocery",
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "channel": "instore",
            "is_return": False,
        },
        {
            "transaction_id": "TX_002",
            "customer_id": "CUS_001",
            "amount_gbp": 5.0,
            "category": "dairy",
            "timestamp": (now - timedelta(days=3)).isoformat(),
            "channel": "instore",
            "is_return": False,
        },
    ]

    df = pl.DataFrame(rows).with_columns(pl.col("timestamp").str.to_datetime())
    profiles = (
        TransactionPipeline()
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm(as_of_date=date.today())
        .to_profiles()
    )

    assert len(profiles) == 1
    # Monetary should be 15.0 (10 + 5), not 1009 (dup 999 excluded)
    from retail.pipeline.pipeline import TransactionPipeline as TLP
    pipeline = TLP()
    rfm_df = (
        pipeline
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm(as_of_date=date.today())
        .result_df()
    )
    monetary = rfm_df["monetary_gbp"][0]
    assert monetary == pytest.approx(15.0)
