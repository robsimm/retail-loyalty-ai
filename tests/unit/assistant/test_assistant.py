"""Tests for ShoppingAssistant — uses mocked Claude client."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from retail.assistant.assistant import ShoppingAssistant
from retail.assistant.domain import ConversationContext
from tests.conftest import make_catalogue, make_profile


def make_mock_response(text: str, tokens_in: int = 100, tokens_out: int = 50) -> MagicMock:
    """Build a mock Anthropic Messages response with a text block."""
    block = MagicMock()
    block.type = "text"
    block.model_dump.return_value = {"type": "text", "text": text}
    response = MagicMock()
    response.content = [block]
    response.usage.input_tokens = tokens_in
    response.usage.output_tokens = tokens_out
    return response


@pytest.mark.unit
def test_assistant_conversation_history_accumulates_across_turns() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("Hi there!")
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    assistant.chat(ctx, "Hello")
    assistant.chat(ctx, "How are you?")

    # user + assistant for each turn = 4 messages
    assert len(ctx.conversation_history) == 4


@pytest.mark.unit
def test_assistant_contract_respects_max_tokens_constraint() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("Here are your recs!")
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    response = assistant.chat(ctx, "What do you recommend?")
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["max_tokens"] <= 1024


@pytest.mark.unit
def test_assistant_returns_assistant_response_object() -> None:
    from retail.assistant.domain import AssistantResponse
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("Hello!")
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    response = assistant.chat(ctx, "Hi")
    assert isinstance(response, AssistantResponse)
    assert response.message == "Hello!"


@pytest.mark.unit
def test_assistant_never_places_order_without_confirmation_in_history() -> None:
    """
    Regression test: assistant should not auto-place orders.
    The system prompt instructs explicit confirmation is required.
    We verify the system prompt includes the guard.
    """
    from retail.assistant.prompts import build_system_prompt
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())
    prompt = build_system_prompt(ctx)
    assert "confirm" in prompt.lower()
    assert "without explicit confirmation" in prompt.lower()
