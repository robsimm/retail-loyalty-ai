"""End-to-end tests: all three systems wired together."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import polars as pl
import pytest

from retail.assistant.assistant import ShoppingAssistant
from retail.assistant.domain import ConversationContext
from retail.pipeline.pipeline import TransactionPipeline
from retail.recommendations.domain import RecommendationRequest
from retail.recommendations.engine import KNNRecommendationEngine
from tests.conftest import make_catalogue


@pytest.mark.e2e
def test_full_system_pipeline_to_recommendations_to_chat() -> None:
    """
    End-to-end: raw transactions → RFM profiles → KNN engine → assistant chat.
    Uses stubbed Claude client to avoid real API calls.
    """
    # 1. Pipeline: transactions → profiles
    now = datetime.now()
    rows = []
    for cust_i in range(15):
        cats = ["grocery", "dairy"] if cust_i % 3 == 0 else ["bakery", "produce"]
        for tx_i in range(10):
            rows.append({
                "transaction_id": f"TX_{cust_i}_{tx_i}",
                "customer_id": f"CUS_{cust_i + 1:03d}",
                "amount_gbp": 20.0 + tx_i * 2,
                "category": cats[tx_i % len(cats)],
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
    assert len(profiles) == 15

    # 2. Fit KNN engine
    catalogue = make_catalogue(n=30)
    engine = KNNRecommendationEngine(catalogue=catalogue)
    engine.fit(profiles)

    recs = engine.predict(RecommendationRequest(customer_id="CUS_001", top_n=5))
    assert len(recs) == 5

    # 3. Chat: wire recommendations into conversation context
    mock_client = MagicMock()
    text_block = MagicMock()
    text_block.type = "text"
    text_block.model_dump.return_value = {
        "type": "text",
        "text": "Here are your top picks based on your profile!",
    }
    mock_response = MagicMock()
    mock_response.content = [text_block]
    mock_response.usage.input_tokens = 150
    mock_response.usage.output_tokens = 60
    mock_client.messages.create.return_value = mock_response

    shopper = profiles[0]
    ctx = ConversationContext(
        session_id="E2E_SES_001",
        profile=shopper,
        recommendations=recs,
    )
    assistant = ShoppingAssistant(catalogue=catalogue, client=mock_client)
    response = assistant.chat(ctx, "What do you recommend for me today?")

    assert "top picks" in response.message.lower() or len(response.message) > 0
    assert len(ctx.conversation_history) == 2
