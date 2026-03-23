from __future__ import annotations

import os
from typing import Any

import anthropic

from retail.assistant.domain import AssistantResponse, ConversationContext, Message
from retail.assistant.parsing import extract_text_content, parse_tool_call
from retail.assistant.prompts import build_system_prompt, sanitize_user_input
from retail.assistant.tools import TOOLS, handle_tool_call
from retail.domain.product import Catalogue

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024


class ShoppingAssistant:
    """
    Claude-powered conversational shopping assistant.

    Manages multi-turn conversation, tool_use dispatch, and session context.
    All Claude API calls are isolated here.
    """

    def __init__(self, catalogue: Catalogue, client: anthropic.Anthropic | None = None) -> None:
        self._catalogue = catalogue
        self._client = client or anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

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
            tools=TOOLS,
            messages=messages,
        )

        total_tokens = response.usage.input_tokens + response.usage.output_tokens
        content: list[dict[str, Any]] = [b.model_dump() for b in response.content]

        # Handle tool use loop (single-step for now)
        tool_result = parse_tool_call(content)
        if tool_result:
            tool_name, tool_input = tool_result
            tool_output = handle_tool_call(tool_name, tool_input, context, self._catalogue)

            # Follow-up call with tool result
            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": next(
                                b.id for b in response.content if b.type == "tool_use"  # type: ignore[union-attr]
                            ),
                            "content": tool_output,
                        }
                    ],
                }
            )

            follow_up = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )
            total_tokens += follow_up.usage.input_tokens + follow_up.usage.output_tokens
            content = [b.model_dump() for b in follow_up.content]

        reply_text = extract_text_content(content)
        context.conversation_history.append(
            Message(role="assistant", content=reply_text, tokens_used=total_tokens)
        )

        return AssistantResponse(message=reply_text, tokens_used=total_tokens)

    def _build_messages(self, context: ConversationContext) -> list[dict[str, Any]]:
        return [
            {"role": m.role, "content": m.content}
            for m in context.conversation_history
        ]
