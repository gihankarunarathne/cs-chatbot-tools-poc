"""Tests for multi-intent decomposition and slot checking logic (no LLM calls)."""

from cschatbot.intents.taxonomy import INTENT_REGISTRY
from cschatbot.models.enums import IntentStatus, IntentType
from cschatbot.models.state import IntentItem


def test_intent_registry_has_all_main_intents():
    for intent in [
        IntentType.ORDER_TRACKING,
        IntentType.REFUND_REQUEST,
        IntentType.WARRANTY_CLAIM,
        IntentType.RETURN_REQUEST,
    ]:
        assert intent in INTENT_REGISTRY
        assert "tools" in INTENT_REGISTRY[intent]
        assert "required_slots" in INTENT_REGISTRY[intent]


def test_slot_check_order_tracking_with_id():
    """Simulate what the intent node does: order_id present → no missing slots."""
    entry = INTENT_REGISTRY[IntentType.ORDER_TRACKING]
    entities = {"order_id": "NXY-1001"}
    missing = [s for s in entry["required_slots"] if s not in entities]
    assert missing == []


def test_slot_check_order_tracking_without_id():
    """order_id absent → missing slot detected."""
    entry = INTENT_REGISTRY[IntentType.ORDER_TRACKING]
    entities = {}
    missing = [s for s in entry["required_slots"] if s not in entities]
    assert "order_id" in missing


def test_multi_intent_items_independent_status():
    """Two intents with different slot completeness should have independent statuses."""
    item_with_slots = IntentItem(
        intent=IntentType.ORDER_TRACKING,
        status=IntentStatus.PENDING,
        entities={"order_id": "NXY-1001"},
        missing_slots=[],
    )
    item_missing_slots = IntentItem(
        intent=IntentType.REFUND_REQUEST,
        status=IntentStatus.NEEDS_INFO,
        entities={},
        missing_slots=["order_id"],
    )
    assert item_with_slots.status == IntentStatus.PENDING
    assert item_missing_slots.status == IntentStatus.NEEDS_INFO
    assert item_with_slots.missing_slots == []
    assert "order_id" in item_missing_slots.missing_slots


def test_refund_requires_order_id():
    entry = INTENT_REGISTRY[IntentType.REFUND_REQUEST]
    assert "order_id" in entry["required_slots"]
    assert "lookup_order" in entry["tools"]
    assert "check_refund_status" in entry["tools"]


def test_warranty_requires_product_id():
    entry = INTENT_REGISTRY[IntentType.WARRANTY_CLAIM]
    assert "product_id" in entry["required_slots"]


def test_general_query_has_no_required_slots():
    entry = INTENT_REGISTRY[IntentType.GENERAL_QUERY]
    assert entry["required_slots"] == []
    assert entry["tools"] == []
