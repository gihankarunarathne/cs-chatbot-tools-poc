from typing import Callable

from ..models.enums import IntentType
from .mocks import (
    check_refund_status,
    check_return_eligibility,
    check_warranty,
    lookup_order,
    lookup_product,
)

TOOL_REGISTRY: dict[str, Callable] = {
    "lookup_order": lookup_order,
    "check_refund_status": check_refund_status,
    "check_warranty": check_warranty,
    "check_return_eligibility": check_return_eligibility,
    "lookup_product": lookup_product,
}


def get_tools_for_intent(intent: IntentType) -> list[str]:
    from ..intents.taxonomy import INTENT_REGISTRY
    return INTENT_REGISTRY.get(intent, {}).get("tools", [])


def call_tool(tool_name: str, **kwargs) -> dict:
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}
    result = fn(**kwargs)
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result
