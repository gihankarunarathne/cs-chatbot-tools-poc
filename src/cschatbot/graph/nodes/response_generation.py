"""Response generation node: calls tools per intent, retrieves SOPs, synthesizes response."""

import json

from langchain_core.messages import AIMessage, SystemMessage

from ...llm.client import get_llm
from ...models.enums import IntentStatus, IntentType
from ...models.state import GraphState, IntentItem
from ...sops.retrieval import retrieve_sop
from ...tools.registry import call_tool, get_tools_for_intent

SYNTHESIS_SYSTEM = """\
You are a helpful customer support agent for Noon, an e-commerce platform in the Middle East.

You will be given:
1. The customer's conversation history
2. For each detected intent: the SOP guidelines + tool results from our systems

Your task is to write a clear, friendly, and professional response that addresses ALL the customer's questions.

Guidelines:
- Be concise but complete
- Address each issue in logical order
- Use the tool data to give specific, accurate answers
- Follow the SOP guidelines strictly
- If a refund/return is in progress, mention timelines
- If handover is needed for any issue, include that at the end
- Do NOT make up information not in the tool results
- Write in English; use a warm, helpful tone
"""


def _build_intent_context(item: IntentItem) -> str:
    parts = [f"### Intent: {item.intent.replace('_', ' ').title()}"]
    parts.append(f"Customer query: {item.query_text}")

    sop_text = retrieve_sop(item.intent)
    parts.append(f"\n**SOP Guidelines:**\n{sop_text}")

    if item.tool_results:
        parts.append("\n**Data from our systems:**")
        for tool_name, result in item.tool_results.items():
            parts.append(f"[{tool_name}]: {json.dumps(result, default=str, indent=2)}")

    return "\n".join(parts)


def response_generation_node(state: GraphState) -> dict:
    updated_intents: list[IntentItem] = []

    for item in state.intents:
        if item.status == IntentStatus.NEEDS_INFO or item.intent == IntentType.OUT_OF_SCOPE:
            updated_intents.append(item)
            continue

        tool_names = get_tools_for_intent(item.intent)
        tool_results: dict[str, dict] = {}

        for tool_name in tool_names:
            # Map required slot names to what each tool expects
            kwargs = _build_tool_kwargs(tool_name, item.entities)
            if kwargs is not None:
                tool_results[tool_name] = call_tool(tool_name, **kwargs)

        updated_item = item.model_copy(update={
            "tool_results": tool_results,
            "status": IntentStatus.RESOLVED,
        })
        updated_intents.append(updated_item)

    # Build synthesis prompt
    intent_contexts = [_build_intent_context(i) for i in updated_intents]
    user_context = "\n\n---\n\n".join(intent_contexts)

    has_handover = any(i.intent == IntentType.OUT_OF_SCOPE for i in updated_intents)

    synthesis_user_msg = f"""Please respond to the customer addressing all their requests.

{user_context}

{"Note: At the end, inform the customer that a human agent will follow up for the issue requiring specialist attention." if has_handover else ""}
"""

    llm = get_llm("response", temperature=0.3)
    history = state.messages[-8:] if len(state.messages) > 1 else state.messages
    messages = [SystemMessage(content=SYNTHESIS_SYSTEM)] + list(history) + [
        {"role": "user", "content": synthesis_user_msg}
    ]

    response = llm.invoke(messages)
    final_text = response.content

    return {
        "intents": updated_intents,
        "final_response": final_text,
        "clarification_question": None,
        "messages": [AIMessage(content=final_text)],
    }


def _build_tool_kwargs(tool_name: str, entities: dict[str, str]) -> dict | None:
    """Map entity dict to the kwargs expected by each tool."""
    mapping = {
        "lookup_order": {"order_id": entities.get("order_id")},
        "check_refund_status": {"order_id": entities.get("order_id")},
        "check_warranty": {"product_id": entities.get("product_id")},
        "check_return_eligibility": {"order_id": entities.get("order_id")},
        "lookup_product": {"product_id": entities.get("product_id")},
    }
    kwargs = mapping.get(tool_name, {})
    # Skip if required arg is missing
    if any(v is None for v in kwargs.values()):
        return None
    return kwargs
