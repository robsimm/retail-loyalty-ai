"""Tests for tool definitions and handler dispatch."""
from __future__ import annotations

import json

import pytest

from retail.assistant.domain import ConversationContext
from retail.assistant.tools import TOOLS, handle_tool_call
from tests.conftest import make_catalogue, make_profile


def make_context() -> ConversationContext:
    return ConversationContext(session_id="SES_001", profile=make_profile())


@pytest.mark.unit
def test_tool_definitions_are_valid_json_schema() -> None:
    """Each tool must have name, description, and input_schema."""
    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        schema = tool["input_schema"]
        assert schema.get("type") == "object"
        assert "properties" in schema
        # Validate it round-trips as JSON
        assert json.loads(json.dumps(tool)) == tool


@pytest.mark.unit
def test_tool_definitions_include_required_tools() -> None:
    names = {t["name"] for t in TOOLS}
    expected = {
        "search_catalogue",
        "get_recommendations",
        "add_to_basket",
        "place_order",
        "check_delivery_slots",
    }
    assert expected.issubset(names)


@pytest.mark.unit
def test_handle_search_catalogue_returns_results() -> None:
    ctx = make_context()
    result = handle_tool_call("search_catalogue", {"category": "dairy"}, ctx, make_catalogue())
    assert "dairy" in result.lower() or "Product" in result


@pytest.mark.unit
def test_handle_check_delivery_slots_returns_available_slots() -> None:
    ctx = make_context()
    result = handle_tool_call("check_delivery_slots", {}, ctx, make_catalogue())
    assert "tomorrow" in result.lower()


@pytest.mark.unit
def test_handle_add_to_basket_adds_item() -> None:
    catalogue = make_catalogue()
    product_id = catalogue.products[0].product_id
    ctx = make_context()
    result = handle_tool_call(
        "add_to_basket", {"product_id": product_id, "quantity": 2}, ctx, catalogue
    )
    assert len(ctx.basket) == 1
    assert "Added" in result


@pytest.mark.unit
def test_handle_place_order_requires_items_in_basket() -> None:
    ctx = make_context()
    result = handle_tool_call(
        "place_order", {"delivery_slot": "tomorrow 9am-1pm"}, ctx, make_catalogue()
    )
    assert "empty" in result.lower()


@pytest.mark.unit
def test_handle_unknown_tool_returns_error_message() -> None:
    ctx = make_context()
    result = handle_tool_call("nonexistent_tool", {}, ctx, make_catalogue())
    assert "Unknown tool" in result


@pytest.mark.unit
def test_place_order_stores_structured_receipt_in_context() -> None:
    catalogue = make_catalogue()
    product = catalogue.products[0]
    ctx = make_context()
    handle_tool_call(
        "add_to_basket", {"product_id": product.product_id, "quantity": 3}, ctx, catalogue
    )
    handle_tool_call("place_order", {"delivery_slot": "tomorrow 9am-1pm"}, ctx, catalogue)
    assert ctx.last_order is not None
    assert str(ctx.last_order["order_id"]).startswith("ORD-")
    assert ctx.last_order["total_gbp"] == pytest.approx(product.price_gbp * 3)
    assert ctx.last_order["delivery"] == "tomorrow 9am-1pm"
    assert ctx.last_order["status"] == "confirmed"
    assert len(ctx.last_order["items"]) == 1  # type: ignore[arg-type]
    item = ctx.last_order["items"][0]  # type: ignore[index]
    assert item["product_name"] == product.name
    assert item["quantity"] == 3
    assert item["line_total_gbp"] == pytest.approx(product.price_gbp * 3)


@pytest.mark.unit
def test_place_order_receipt_items_match_basket_contents() -> None:
    catalogue = make_catalogue()
    ctx = make_context()
    handle_tool_call(
        "add_to_basket",
        {"product_id": catalogue.products[0].product_id, "quantity": 1},
        ctx,
        catalogue,
    )
    handle_tool_call(
        "add_to_basket",
        {"product_id": catalogue.products[1].product_id, "quantity": 2},
        ctx,
        catalogue,
    )
    handle_tool_call("place_order", {"delivery_slot": "tomorrow 1pm-5pm"}, ctx, catalogue)
    assert ctx.last_order is not None
    assert len(ctx.last_order["items"]) == 2  # type: ignore[arg-type]
    names = {i["product_name"] for i in ctx.last_order["items"]}  # type: ignore[union-attr]
    assert catalogue.products[0].name in names
    assert catalogue.products[1].name in names


@pytest.mark.unit
def test_place_order_clears_basket_after_storing_receipt() -> None:
    catalogue = make_catalogue()
    ctx = make_context()
    handle_tool_call(
        "add_to_basket",
        {"product_id": catalogue.products[0].product_id, "quantity": 1},
        ctx,
        catalogue,
    )
    handle_tool_call("place_order", {"delivery_slot": "tomorrow 9am-1pm"}, ctx, catalogue)
    assert ctx.basket == []
    assert ctx.last_order is not None
