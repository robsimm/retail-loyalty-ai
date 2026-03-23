from __future__ import annotations

import json as _json
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


def parse_all_tool_calls(
    response_content: list[dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Return (tool_use_id, tool_name, tool_input) for every tool_use block."""
    return [
        (block["id"], block["name"], block.get("input", {}))
        for block in response_content
        if block.get("type") == "tool_use"
    ]


def extract_text_content(response_content: list[dict[str, Any]]) -> str:
    """Extract all text blocks from a Claude API response content list."""
    parts: list[str] = []
    for block in response_content:
        if block.get("type") == "text":
            parts.append(block["text"])
    return "\n".join(parts)


def parse_assistant_response(raw: str) -> tuple[str, list[Any]]:
    """
    Extract (message, pills) from a Claude reply.

    Handles bare JSON, markdown code-fenced JSON, and JSON embedded after
    narrative prose. Falls back to (raw, []) if no valid JSON is found.
    """
    text = raw.strip()

    # Strip markdown code fence
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()

    # Find first JSON object in text (handles narrative prefix and trailing fences)
    brace_idx = text.find("{")
    if brace_idx != -1:
        last_brace = text.rfind("}")
        if last_brace > brace_idx:
            candidate = text[brace_idx : last_brace + 1]
            try:
                parsed = _json.loads(candidate)
                return parsed.get("message", raw), parsed.get("pills", [])
            except (ValueError, KeyError):
                pass

    return raw, []
