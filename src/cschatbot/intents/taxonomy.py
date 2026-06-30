from ..models.enums import IntentType

INTENT_REGISTRY: dict[IntentType, dict] = {
    IntentType.ORDER_TRACKING: {
        "description": "Customer wants delivery status, location, or ETA of an order.",
        "tools": ["lookup_order"],
        "sop_key": "order_tracking",
        "required_slots": ["order_id"],
    },
    IntentType.REFUND_REQUEST: {
        "description": "Customer asks about refund status or wants to request a refund.",
        "tools": ["lookup_order", "check_refund_status"],
        "sop_key": "refund",
        "required_slots": ["order_id"],
    },
    IntentType.WARRANTY_CLAIM: {
        "description": "Customer wants to claim warranty or check warranty coverage.",
        "tools": ["check_warranty"],
        "sop_key": "warranty",
        "required_slots": ["product_id"],
    },
    IntentType.RETURN_REQUEST: {
        "description": "Customer wants to return or exchange an item.",
        "tools": ["lookup_order", "check_return_eligibility"],
        "sop_key": "return",
        "required_slots": ["order_id"],
    },
    IntentType.PRODUCT_INFO: {
        "description": "Questions about product specs, availability, or price.",
        "tools": ["lookup_product"],
        "sop_key": "product_info",
        "required_slots": ["product_id"],
    },
    IntentType.GENERAL_QUERY: {
        "description": "General policy, how-to, or account questions.",
        "tools": [],
        "sop_key": "general",
        "required_slots": [],
    },
    IntentType.OUT_OF_SCOPE: {
        "description": "Outside support scope or customer explicitly requests a human agent.",
        "tools": [],
        "sop_key": "handover",
        "required_slots": [],
    },
}
