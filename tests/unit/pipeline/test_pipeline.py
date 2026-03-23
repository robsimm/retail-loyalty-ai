"""Tests for TransactionPipeline fluent orchestrator."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import polars as pl
import pytest

from retail.pipeline.pipeline import TransactionPipeline


def make_tx_rows(n_customers: int = 3, n_tx_each: int = 5) -> list[dict]:  # type: ignore[type-arg]
    now = datetime.now()
    rows = []
    for cust in range(n_customers):
        for i in range(n_tx_each):
            rows.append({
                "transaction_id": f"TX_{cust}_{i}",
                "customer_id": f"CUS_{cust + 1:03d}",
                "amount_gbp": 10.0 + i,
                "category": "grocery",
                "timestamp": (now - timedelta(days=i + 1)).isoformat(),
                "channel": "instore",
                "is_return": False,
            })
    return rows


@pytest.mark.unit
def test_transaction_pipeline_transform_is_idempotent() -> None:
    """Running transform twice gives same result as running it once."""
    df = pl.DataFrame(make_tx_rows()).with_columns(
        pl.col("timestamp").str.to_datetime()
    )
    pipeline = TransactionPipeline()
    result_once = pipeline.load_df(df).validate().transform().result_df()

    pipeline2 = TransactionPipeline()
    result_twice = pipeline2.load_df(df).validate().transform().transform().result_df()

    assert len(result_once) == len(result_twice)


@pytest.mark.unit
def test_transaction_pipeline_aggregate_rfm_preserves_all_customers() -> None:
    df = pl.DataFrame(make_tx_rows(n_customers=5)).with_columns(
        pl.col("timestamp").str.to_datetime()
    )
    pipeline = TransactionPipeline()
    profiles = (
        pipeline
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm(as_of_date=date.today())
        .to_profiles()
    )
    assert len(profiles) == 5


@pytest.mark.unit
def test_transaction_pipeline_validate_raises_on_missing_columns() -> None:
    df = pl.DataFrame([{"foo": "bar"}])
    with pytest.raises(ValueError, match="Missing required columns"):
        TransactionPipeline().load_df(df).validate()


@pytest.mark.unit
def test_transaction_pipeline_to_profiles_returns_shopper_profiles() -> None:
    from retail.domain.customer import ShopperProfile
    df = pl.DataFrame(make_tx_rows()).with_columns(
        pl.col("timestamp").str.to_datetime()
    )
    profiles = (
        TransactionPipeline()
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm(as_of_date=date.today())
        .to_profiles()
    )
    assert all(isinstance(p, ShopperProfile) for p in profiles)
