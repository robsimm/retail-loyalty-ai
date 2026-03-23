from __future__ import annotations

from typing import Any

from retail.assistant.domain import ConversationContext
from retail.domain.order import DeliverySlot, Order, OrderItem
from retail.domain.product import Catalogue

TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_catalogue",
        "description": "Search the product catalogue by name or category",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "category": {"type": "string", "description": "Filter by category"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "get_recommendations",
        "description": "Get personalised recommendations for the current customer",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "default": 5},
                "high_consideration_only": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "add_to_basket",
        "description": "Add a product to the customer's current basket",
        "input_schema": {
            "type": "object",
            "required": ["product_id", "quantity"],
            "properties": {
                "product_id": {"type": "string"},
                "quantity": {"type": "integer"},
            },
        },
    },
    {
        "name": "place_order",
        "description": "Place the current basket as an order with a delivery slot",
        "input_schema": {
            "type": "object",
            "required": ["delivery_slot"],
            "properties": {
                "delivery_slot": {
                    "type": "string",
                    "description": "e.g. 'tomorrow 9am-1pm' or '2026-03-24 morning'",
                }
            },
        },
    },
    {
        "name": "check_delivery_slots",
        "description": "Check available delivery slots for the next 3 days",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


def handle_tool_call(
    tool_name: str,
    tool_input: dict[str, Any],
    context: ConversationContext,
    catalogue: Catalogue,
) -> str:
    """Dispatch tool calls and return a string result for Claude."""
    if tool_name == "search_catalogue":
        products = catalogue.search(
            query=tool_input.get("query", ""),
            category=tool_input.get("category", ""),
            limit=tool_input.get("limit", 10),
        )
        if not products:
            return "No products found."
        lines = [f"- {p.product_id}: {p.name} ({p.category}) £{p.price_gbp:.2f}" for p in products]
        return "\n".join(lines)

    if tool_name == "get_recommendations":
        recs = context.recommendations[: tool_input.get("top_n", 5)]
        if not recs:
            return "No recommendations available yet."
        lines = [f"- {r.product_id}: {r.product_name} ({r.category})" for r in recs]
        return "\n".join(lines)

    if tool_name == "add_to_basket":
        product_id = tool_input["product_id"]
        quantity = tool_input["quantity"]
        product = catalogue.find_by_id(product_id)
        if product is None:
            return f"Product {product_id} not found in catalogue."
        context.basket.append(
            {
                "product_id": product_id,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price_gbp": product.price_gbp,
            }
        )
        return f"Added {quantity}x {product.name} to basket."

    if tool_name == "place_order":
        if not context.basket:
            return "Basket is empty. Add items first."
        slot_str = tool_input["delivery_slot"]
        items = [
            OrderItem(
                product_id=str(item["product_id"]),
                product_name=str(item["product_name"]),
                quantity=int(item["quantity"]),  # type: ignore[call-overload]
                unit_price_gbp=float(item["unit_price_gbp"]),  # type: ignore[arg-type]
            )
            for item in context.basket
        ]
        slot = DeliverySlot(slot_id="SLOT-001", date=slot_str, time_window=slot_str)
        order = Order(
            order_id=f"ORD-{context.session_id[:8]}",
            customer_id=context.profile.customer_id,
            items=items,
            delivery_slot=slot,
            status="confirmed",
        )
        context.last_order = {
            "order_id": order.order_id,
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price_gbp": item.unit_price_gbp,
                    "line_total_gbp": item.line_total_gbp,
                }
                for item in items
            ],
            "total_gbp": order.total_gbp,
            "delivery": slot_str,
            "status": order.status,
        }
        context.basket.clear()
        return f"Order {order.order_id} placed. Total: £{order.total_gbp:.2f}. Delivery: {slot_str}"

    if tool_name == "check_delivery_slots":
        return (
            "Available slots:\n"
            "- tomorrow 9am-1pm\n"
            "- tomorrow 1pm-5pm\n"
            "- day after tomorrow 9am-1pm\n"
            "- day after tomorrow 1pm-5pm"
        )

    return f"Unknown tool: {tool_name}"
