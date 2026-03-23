"""Tests for response parsing functions."""
from __future__ import annotations

import pytest

from retail.assistant.parsing import extract_text_content, parse_tool_call


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
