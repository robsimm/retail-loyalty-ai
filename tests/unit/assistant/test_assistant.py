"""Tests for ShoppingAssistant — uses mocked Claude client."""
from __future__ import annotations

from unittest.mock import MagicMock

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

    assistant.chat(ctx, "What do you recommend?")
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
def test_assistant_strips_markdown_code_fence_and_parses_json() -> None:
    fenced = "```json\n{\"message\": \"hello\", \"pills\": []}\n```"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response(fenced)
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    response = assistant.chat(ctx, "Hi")
    assert response.message == "hello"
    assert response.pills == []


@pytest.mark.unit
def test_assistant_falls_back_gracefully_on_non_json_reply() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("Plain text reply")
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    response = assistant.chat(ctx, "Hi")
    assert response.message == "Plain text reply"
    assert response.pills == []


@pytest.mark.unit
def test_assistant_populates_pills_from_json_response() -> None:
    payload = (
        '{"message": "Here are your picks:", '
        '"pills": [{"label": "Dairy Item 1", "action": "Add PRD_00001 to my basket"}]}'
    )
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response(payload)
    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    response = assistant.chat(ctx, "What do you recommend?")
    assert response.message == "Here are your picks:"
    assert len(response.pills) == 1
    assert response.pills[0]["label"] == "Dairy Item 1"
    assert response.pills[0]["action"] == "Add PRD_00001 to my basket"


@pytest.mark.unit
def test_assistant_multi_step_tool_loop_populates_basket() -> None:
    """get_recommendations → add_to_basket: basket must be populated after both tool calls."""
    def make_tool_response(tool_id: str, name: str, input_dict: dict) -> MagicMock:
        block = MagicMock()
        block.type = "tool_use"
        block.id = tool_id
        block.name = name
        block.input = input_dict
        block.model_dump.return_value = {
            "type": "tool_use", "id": tool_id, "name": name, "input": input_dict
        }
        resp = MagicMock()
        resp.content = [block]
        resp.usage.input_tokens = 50
        resp.usage.output_tokens = 20
        return resp

    recs_response = make_tool_response("c1", "get_recommendations", {"top_n": 3})
    add_response = make_tool_response(
        "c2", "add_to_basket", {"product_id": "PRD_001", "quantity": 1}
    )
    final_response = make_mock_response('{"message": "Done! Added to basket.", "pills": []}')

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [recs_response, add_response, final_response]

    assistant = ShoppingAssistant(catalogue=make_catalogue(), client=mock_client)
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())

    response = assistant.chat(ctx, "Buy my usual groceries")

    assert response.message == "Done! Added to basket."
    assert len(ctx.basket) == 1
    assert ctx.basket[0]["product_id"] == "PRD_001"


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
