"""Intent detection node: classifies customer intent(s), extracts entities, checks slots."""

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from ...intents.taxonomy import INTENT_REGISTRY
from ...llm.client import get_llm
from ...models.enums import IntentStatus, IntentType
from ...models.state import GraphState, IntentItem

SYSTEM_PROMPT = """\
You are an intent detection system for a customer support chatbot at Noon, an e-commerce platform.

Your job is to analyze the customer's latest message (in the context of the conversation history) and extract ALL intents.

Available intents:
- order_tracking: Customer wants delivery status / ETA of an order
- refund_request: Customer asks about refund status or wants to request one
- warranty_claim: Customer wants to claim warranty or check coverage
- return_request: Customer wants to return or exchange an item
- product_info: Questions about product specs, availability, or price
- general_query: General policy or account questions
- out_of_scope: Outside support scope or customer wants a human agent

For each intent, extract relevant entities:
- order_id: e.g. "NXY-1001" (normalize to uppercase)
- product_id: e.g. "PRD-A"
- Any other relevant identifiers

Support multi-intent: a single message can have multiple intents (e.g. tracking one order AND asking for refund on another).

Return a JSON object with a list of detected intents.
"""


class DetectedIntent(BaseModel):
    intent: IntentType
    entities: dict[str, str]
    query_text: str


class IntentDetectionResult(BaseModel):
    intents: list[DetectedIntent]


def intent_detection_node(state: GraphState) -> dict:
    llm = get_llm("intent", temperature=0.0)
    structured_llm = llm.with_structured_output(IntentDetectionResult)

    # Build context from recent history (last 6 messages)
    history = state.messages[-6:] if len(state.messages) > 1 else state.messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(history)

    result: IntentDetectionResult = structured_llm.invoke(messages)

    if not result.intents:
        result.intents = [DetectedIntent(
            intent=IntentType.GENERAL_QUERY,
            entities={},
            query_text="Customer sent an unrecognized message",
        )]

    intent_items: list[IntentItem] = []
    missing_info_parts: list[str] = []

    for detected in result.intents:
        registry_entry = INTENT_REGISTRY.get(detected.intent, {})
        required_slots = registry_entry.get("required_slots", [])
        missing_slots = [s for s in required_slots if s not in detected.entities]

        status = IntentStatus.NEEDS_INFO if missing_slots else IntentStatus.PENDING

        item = IntentItem(
            intent=detected.intent,
            status=status,
            entities=detected.entities,
            missing_slots=missing_slots,
            query_text=detected.query_text,
        )
        intent_items.append(item)

        if missing_slots:
            slot_labels = {"order_id": "order ID", "product_id": "product ID"}
            readable_slots = [slot_labels.get(s, s) for s in missing_slots]
            intent_label = detected.intent.replace("_", " ")
            missing_info_parts.append(
                f"For your **{intent_label}**, could you please provide: {', '.join(readable_slots)}?"
            )

    # If any intent is missing required info, compose one consolidated clarification question
    clarification = None
    if missing_info_parts:
        if len(missing_info_parts) == 1:
            clarification = missing_info_parts[0]
        else:
            clarification = "I'd love to help with all your requests! I just need a few details:\n\n" + \
                "\n".join(f"• {p}" for p in missing_info_parts)

    return {
        "intents": intent_items,
        "clarification_question": clarification,
        "final_response": None,
        "requires_handover": any(i.intent == IntentType.OUT_OF_SCOPE for i in intent_items),
    }
