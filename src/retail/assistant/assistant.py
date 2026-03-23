from __future__ import annotations

import os
from typing import Any

import anthropic

from retail.assistant.domain import AssistantResponse, ConversationContext, Message
from retail.assistant.parsing import (
    extract_text_content,
    parse_all_tool_calls,
    parse_assistant_response,
)
from retail.assistant.prompts import build_system_prompt, sanitize_user_input
from retail.assistant.tools import TOOLS, handle_tool_call
from retail.domain.product import Catalogue

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
MAX_TOOL_ITERATIONS = 5


class ShoppingAssistant:
    """
    Claude-powered conversational shopping assistant.

    Manages multi-turn conversation, tool_use dispatch, and session context.
    All Claude API calls are isolated here.
    """

    def __init__(self, catalogue: Catalogue, client: anthropic.Anthropic | None = None) -> None:
        self._catalogue = catalogue
        self._client = client or anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )

    def chat(self, context: ConversationContext, user_message: str) -> AssistantResponse:
        """
        Process one turn of conversation.

        Appends to context.conversation_history in-place.
        Returns the assistant response.
        """
        clean_input = sanitize_user_input(user_message)
        context.conversation_history.append(Message(role="user", content=clean_input))

        messages = self._build_messages(context)
        system_prompt = build_system_prompt(context)

        response = self._client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=TOOLS,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )

        total_tokens = response.usage.input_tokens + response.usage.output_tokens
        content: list[dict[str, Any]] = [b.model_dump() for b in response.content]

        # Tool use loop — handles multi-step and parallel tool calls
        for _ in range(MAX_TOOL_ITERATIONS):
            tool_calls = parse_all_tool_calls(content)
            if not tool_calls:
                break

            messages.append({"role": "assistant", "content": response.content})
            tool_results = [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": handle_tool_call(tool_name, tool_input, context, self._catalogue),
                }
                for tool_id, tool_name, tool_input in tool_calls
            ]
            messages.append({"role": "user", "content": tool_results})

            response = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=TOOLS,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )
            total_tokens += response.usage.input_tokens + response.usage.output_tokens
            content = [b.model_dump() for b in response.content]

        reply_text = extract_text_content(content)
        message, pills = parse_assistant_response(reply_text)

        context.conversation_history.append(
            Message(role="assistant", content=message, tokens_used=total_tokens)
        )

        return AssistantResponse(message=message, pills=pills, tokens_used=total_tokens)

    def _build_messages(self, context: ConversationContext) -> list[dict[str, Any]]:
        return [
            {"role": m.role, "content": m.content}
            for m in context.conversation_history
        ]
