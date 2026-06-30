from enum import StrEnum


class IntentType(StrEnum):
    ORDER_TRACKING = "order_tracking"
    REFUND_REQUEST = "refund_request"
    WARRANTY_CLAIM = "warranty_claim"
    RETURN_REQUEST = "return_request"
    PRODUCT_INFO = "product_info"
    GENERAL_QUERY = "general_query"
    CLARIFICATION_NEEDED = "clarification_needed"
    OUT_OF_SCOPE = "out_of_scope"


class IntentStatus(StrEnum):
    PENDING = "pending"
    NEEDS_INFO = "needs_info"
    RESOLVED = "resolved"
