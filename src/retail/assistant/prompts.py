from __future__ import annotations

from retail.assistant.domain import ConversationContext

MAX_SYSTEM_PROMPT_TOKENS = 2000


def build_system_prompt(context: ConversationContext) -> str:
    """Build the system prompt for the Claude shopping assistant."""
    profile = context.profile
    top_recs = context.recommendations[:3]
    rec_names = ", ".join(r.product_name for r in top_recs) if top_recs else "none yet"

    return (
        f"You are a friendly shopping assistant for a loyalty scheme.\n"
        f"Help customers order items using their personal preferences.\n\n"
        f"Customer: {profile.customer_id}\n"
        f"Loyalty tier: {profile.rfm_segment}\n"
        f"Top categories: {', '.join(profile.preferred_categories) or 'unknown'}\n"
        f"Recommendations today: {rec_names}\n\n"
        f"When a customer says something like 'buy my usual items', use "
        f"get_recommendations then add_to_basket for their top items.\n"
        f"Always confirm before placing an order. Never place an order "
        f"without explicit confirmation from the customer."
    )


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def sanitize_user_input(text: str) -> str:
    """
    Remove obvious prompt injection attempts.
    Strips instructions that try to override the system prompt.
    """
    injection_markers = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard your instructions",
        "forget your instructions",
        "new instructions:",
        "system prompt:",
        "you are now",
    ]
    lower = text.lower()
    for marker in injection_markers:
        if marker in lower:
            return "[input removed: possible prompt injection attempt]"
    return text
