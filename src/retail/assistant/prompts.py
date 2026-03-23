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
        f"without explicit confirmation from the customer.\n\n"
        f"RESPONSE FORMAT: Always reply in valid JSON with this exact shape:\n"
        f'  {{"message": "<your reply>", "pills": [{{"label": "...", "action": "..."}}]}}\n\n'
        f"Rules for 'message': write a natural conversational reply. When presenting "
        f"products, lead with a brief personal sentence (e.g. 'Based on your shopping "
        f"history, here are my top picks for you today:') — do NOT list the products "
        f"in the message text.\n\n"
        f"Rules for 'pills': include one pill per product when presenting recommendations "
        f"or search results. Each label should be the product name only (short). Each "
        f"action should be the literal message to send on click. "
        f"IMPORTANT: for add-to-basket actions use the product_id not the name "
        f"(e.g. 'Add PRD_00002 to my basket'). "
        f"Use an empty list when no products are being offered."
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
