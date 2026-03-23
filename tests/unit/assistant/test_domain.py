"""Tests for assistant domain models."""
from __future__ import annotations

import pytest
from datetime import datetime

from retail.assistant.domain import AssistantResponse, ConversationContext, Message
from tests.conftest import make_profile


@pytest.mark.unit
def test_message_defaults_to_current_timestamp() -> None:
    msg = Message(role="user", content="hello")
    assert isinstance(msg.timestamp, datetime)


@pytest.mark.unit
def test_conversation_context_starts_with_empty_history() -> None:
    ctx = ConversationContext(session_id="SES_001", profile=make_profile())
    assert ctx.conversation_history == []
    assert ctx.basket == []


@pytest.mark.unit
def test_assistant_response_defaults() -> None:
    resp = AssistantResponse(message="Hello!")
    assert resp.recommended_product_ids == []
    assert resp.follow_up_question is None
    assert resp.order is None
    assert resp.tokens_used == 0
