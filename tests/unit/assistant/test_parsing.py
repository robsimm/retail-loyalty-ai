"""Tests for response parsing functions."""
from __future__ import annotations

import pytest

from retail.assistant.parsing import (
    extract_text_content,
    parse_all_tool_calls,
    parse_assistant_response,
    parse_tool_call,
)


@pytest.mark.unit
def test_parse_tool_call_returns_correct_function_name() -> None:
    content = [
        {
            "type": "tool_use",
            "id": "call_001",
            "name": "search_catalogue",
            "input": {"query": "milk"},
        },
    ]
    result = parse_tool_call(content)
    assert result is not None
    tool_name, tool_input = result
    assert tool_name == "search_catalogue"
    assert tool_input == {"query": "milk"}


@pytest.mark.unit
def test_parse_tool_call_returns_none_when_no_tool_use() -> None:
    content = [{"type": "text", "text": "Hello there!"}]
    assert parse_tool_call(content) is None


@pytest.mark.unit
def test_parse_tool_call_returns_first_tool_when_multiple() -> None:
    content = [
        {"type": "tool_use", "id": "call_001", "name": "first_tool", "input": {}},
        {"type": "tool_use", "id": "call_002", "name": "second_tool", "input": {}},
    ]
    result = parse_tool_call(content)
    assert result is not None
    assert result[0] == "first_tool"


@pytest.mark.unit
def test_parse_all_tool_calls_returns_all_blocks() -> None:
    content = [
        {"type": "tool_use", "id": "c1", "name": "get_recommendations", "input": {"top_n": 5}},
        {"type": "tool_use", "id": "c2", "name": "add_to_basket",
         "input": {"product_id": "PRD_001", "quantity": 1}},
    ]
    result = parse_all_tool_calls(content)
    assert len(result) == 2
    assert result[0] == ("c1", "get_recommendations", {"top_n": 5})
    assert result[1] == ("c2", "add_to_basket", {"product_id": "PRD_001", "quantity": 1})


@pytest.mark.unit
def test_parse_all_tool_calls_returns_empty_for_no_tool_use() -> None:
    content = [{"type": "text", "text": "Hello"}]
    assert parse_all_tool_calls(content) == []


@pytest.mark.unit
def test_extract_text_content_joins_all_text_blocks() -> None:
    content = [
        {"type": "text", "text": "Hello"},
        {"type": "tool_use", "id": "x", "name": "foo", "input": {}},
        {"type": "text", "text": "World"},
    ]
    result = extract_text_content(content)
    assert "Hello" in result
    assert "World" in result


@pytest.mark.unit
def test_extract_text_content_returns_empty_for_no_text() -> None:
    content = [{"type": "tool_use", "id": "x", "name": "foo", "input": {}}]
    assert extract_text_content(content) == ""


@pytest.mark.unit
def test_parse_assistant_response_bare_json() -> None:
    raw = '{"message": "Hello!", "pills": []}'
    msg, pills = parse_assistant_response(raw)
    assert msg == "Hello!"
    assert pills == []


@pytest.mark.unit
def test_parse_assistant_response_code_fenced_json() -> None:
    raw = '```json\n{"message": "Hello!", "pills": []}\n```'
    msg, pills = parse_assistant_response(raw)
    assert msg == "Hello!"
    assert pills == []


@pytest.mark.unit
def test_parse_assistant_response_narrative_prefix() -> None:
    raw = 'Here are your picks! {"message": "Here are your picks!", "pills": []}'
    msg, pills = parse_assistant_response(raw)
    assert msg == "Here are your picks!"
    assert pills == []


@pytest.mark.unit
def test_parse_assistant_response_plain_text_fallback() -> None:
    raw = "Plain text reply"
    msg, pills = parse_assistant_response(raw)
    assert msg == raw
    assert pills == []


@pytest.mark.unit
def test_parse_assistant_response_narrative_prefix_with_code_fence() -> None:
    raw = 'Great news! ```json\n{"message": "Done!", "pills": []}\n```'
    msg, pills = parse_assistant_response(raw)
    assert msg == "Done!"
    assert pills == []
