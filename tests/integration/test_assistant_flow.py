"""Integration tests: multi-turn conversation (stubbed Claude client)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from retail.assistant.assistant import ShoppingAssistant
from retail.assistant.domain import ConversationContext
from tests.conftest import make_catalogue, make_profile


def make_text_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.model_dump.return_value = {"type": "text", "text": text}
    resp = MagicMock()
    resp.content = [block]
    resp.usage.input_tokens = 100
    resp.usage.output_tokens = 50
    return resp


@pytest.mark.integration
def test_assistant_flow_multi_turn_accumulates_history() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_text_response("Here are your options!")
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_INT_001", profile=make_profile())

    assistant.chat(ctx, "What's available in dairy?")
    assistant.chat(ctx, "Add some milk please")
    assistant.chat(ctx, "What's in my basket?")

    assert len(ctx.conversation_history) == 6  # 3 user + 3 assistant


@pytest.mark.integration
def test_assistant_flow_tool_dispatch_add_to_basket() -> None:
    """Test that add_to_basket tool call is dispatched and basket updated."""
    catalogue = make_catalogue(n=10)
    product_id = catalogue.products[0].product_id

    # Simulate Claude responding with a tool_use block
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "call_001"
    tool_block.model_dump.return_value = {
        "type": "tool_use",
        "id": "call_001",
        "name": "add_to_basket",
        "input": {"product_id": product_id, "quantity": 1},
    }

    text_block = MagicMock()
    text_block.type = "text"
    text_block.model_dump.return_value = {"type": "text", "text": "I've added it!"}

    first_response = MagicMock()
    first_response.content = [tool_block]
    first_response.usage.input_tokens = 100
    first_response.usage.output_tokens = 20

    second_response = MagicMock()
    second_response.content = [text_block]
    second_response.usage.input_tokens = 120
    second_response.usage.output_tokens = 30

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [first_response, second_response]

    assistant = ShoppingAssistant(catalogue=catalogue, client=mock_client)
    ctx = ConversationContext(session_id="SES_INT_002", profile=make_profile())
    response = assistant.chat(ctx, f"Add {product_id} to my basket")

    assert len(ctx.basket) == 1
    assert response.message == "I've added it!"
