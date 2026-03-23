from __future__ import annotations

from typing import Any


def parse_tool_call(response_content: list[dict[str, Any]]) -> tuple[str, dict[str, Any]] | None:
    """
    Extract the first tool_use block from a Claude API response content list.

    Returns (tool_name, tool_input) or None if no tool call present.
    """
    for block in response_content:
        if block.get("type") == "tool_use":
            return block["name"], block.get("input", {})
    return None


def extract_text_content(response_content: list[dict[str, Any]]) -> str:
    """Extract all text blocks from a Claude API response content list."""
    parts: list[str] = []
    for block in response_content:
        if block.get("type") == "text":
            parts.append(block["text"])
    return "\n".join(parts)
