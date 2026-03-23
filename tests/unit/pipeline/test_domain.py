"""Tests for pipeline domain models. TDD: tests written first."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from retail.pipeline.domain import RFMSegment, Transaction, TransactionBatch


@pytest.mark.unit
def test_transaction_creation_with_valid_data_succeeds() -> None:
    tx = Transaction(
        transaction_id="TX_001",
        customer_id="CUS_001",
        amount_gbp=25.50,
        category="grocery",
        timestamp=datetime.now() - timedelta(days=1),
    )
    assert tx.transaction_id == "TX_001"
    assert tx.amount_gbp == 25.50


@pytest.mark.unit
def test_transaction_creation_with_negative_amount_raises_value_error() -> None:
    with pytest.raises(ValueError, match="amount_gbp must be >= 0"):
        Transaction(
            transaction_id="TX_001",
            customer_id="CUS_001",
            amount_gbp=-5.0,
            category="grocery",
            timestamp=datetime.now() - timedelta(days=1),
        )


@pytest.mark.unit
def test_transaction_creation_with_future_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="timestamp must not be in the future"):
        Transaction(
            transaction_id="TX_001",
            customer_id="CUS_001",
            amount_gbp=10.0,
            category="grocery",
            timestamp=datetime.now() + timedelta(days=1),
        )


@pytest.mark.unit
def test_rfm_segment_defaults_to_at_risk() -> None:
    seg = RFMSegment(
        customer_id="CUS_001",
        recency_days=30,
        frequency_count=5,
        monetary_gbp=100.0,
    )
    assert seg.segment == "at_risk"


@pytest.mark.unit
def test_rfm_segment_champions_label_accepted() -> None:
    seg = RFMSegment(
        customer_id="CUS_001",
        recency_days=2,
        frequency_count=50,
        monetary_gbp=1000.0,
        segment="champions",
    )
    assert seg.segment == "champions"


@pytest.mark.unit
def test_transaction_batch_count_reflects_transactions() -> None:
    txs = [
        Transaction(
            transaction_id=f"TX_{i}",
            customer_id="CUS_001",
            amount_gbp=10.0,
            category="grocery",
            timestamp=datetime.now() - timedelta(days=1),
        )
        for i in range(3)
    ]
    batch = TransactionBatch(transactions=txs)
    assert batch.count == 3
