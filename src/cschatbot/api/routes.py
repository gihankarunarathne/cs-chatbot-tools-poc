from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage
from openai import APIError, APITimeoutError, RateLimitError

from ..config import settings
from ..logging_setup import get_logger
from ..models.api import ChatRequest, ChatResponse, IntentDebug, ToolCallDebug, TurnDebug
from ..models.enums import IntentStatus
from ..tools.registry import _build_tool_kwargs_for_debug
from .session import list_sessions, new_session_id, register_session

router = APIRouter()
logger = get_logger(__name__)

DEMO_SCENARIOS = [
    {
        "id": "order_tracking",
        "title": "Order Tracking",
        "description": "Customer tracking an in-transit order",
        "turns": [
            "Where is my order NXY-1001? I ordered it 3 days ago.",
        ],
    },
    {
        "id": "refund_inquiry",
        "title": "Refund Status",
        "description": "Customer checking refund on a delivered order",
        "turns": [
            "I returned my headphones last week. Has my refund for order NXY-2002 been processed?",
        ],
    },
    {
        "id": "multi_intent",
        "title": "Multi-Intent: Track + Refund",
        "description": "Customer asks about two different orders in one message",
        "turns": [
            "Hey, where is order NXY-1001 and also did my refund for NXY-2002 go through?",
        ],
    },
    {
        "id": "clarification_flow",
        "title": "Clarification Flow",
        "description": "Customer forgets order ID — bot asks, then resolves",
        "turns": [
            "I want to track my order please",
            "It's NXY-3003",
        ],
    },
    {
        "id": "warranty_claim",
        "title": "Warranty Claim",
        "description": "Customer wants to claim warranty on a product",
        "turns": [
            "My Samsung Galaxy stopped charging. I want to claim warranty on product PRD-A.",
        ],
    },
    {
        "id": "return_request",
        "title": "Return Request",
        "description": "Customer wants to return a delivered order",
        "turns": [
            "I'd like to return my order NXY-2002. The headphones don't fit properly.",
        ],
    },
    {
        "id": "human_escalation",
        "title": "Human Escalation",
        "description": "Customer insists on speaking to a human agent",
        "turns": [
            "I've been waiting 3 weeks for my refund. This is unacceptable. I want to speak to a manager right now.",
        ],
    },
]


@router.get("/health")
async def health():
    configured = bool(settings.openai_api_key)
    return {
        "status": "ok" if configured else "misconfigured",
        "openai_configured": configured,
        "intent_model": settings.intent_model,
        "response_model": settings.response_model,
    }


@router.get("/demo/scenarios")
async def get_demo_scenarios():
    return {"scenarios": DEMO_SCENARIOS}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    graph = request.app.state.graph

    session_id = body.session_id or new_session_id()
    register_session(session_id)
    log = get_logger(__name__, session_id=session_id)

    config = {"configurable": {"thread_id": session_id}}
    graph_input = {"messages": [HumanMessage(content=body.message)]}

    log.info("chat turn received (%d chars)", len(body.message))

    try:
        final_state = await graph.ainvoke(graph_input, config=config)
    except (RateLimitError, APITimeoutError) as e:
        log.warning("LLM transiently unavailable: %s", e)
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily unavailable. Please try again.",
        ) from e
    except APIError as e:
        log.error("LLM API error: %s", e)
        raise HTTPException(
            status_code=502,
            detail="The assistant failed to process your message.",
        ) from e

    response_text = final_state.get("final_response") or "I'm sorry, I couldn't process your request."
    intents = final_state.get("intents", [])
    requires_handover = final_state.get("requires_handover", False)
    awaiting_clarification = bool(final_state.get("clarification_question")) and not requires_handover

    intent_debug = [
        IntentDebug(
            intent=i.intent,
            status=i.status,
            entities=i.entities,
            missing_slots=i.missing_slots,
        )
        for i in intents
    ]

    # Build tool call debug from resolved intents
    tool_calls: list[ToolCallDebug] = []
    for item in intents:
        if item.status == IntentStatus.RESOLVED:
            for tool_name, output in item.tool_results.items():
                inputs = _build_tool_kwargs_for_debug(tool_name, item.entities)
                tool_calls.append(ToolCallDebug(
                    tool_name=tool_name,
                    inputs=inputs,
                    output=output,
                    intent=item.intent,
                ))

    # Infer which nodes executed this turn
    if awaiting_clarification:
        nodes_executed = ["intent_detection", "clarify"]
    else:
        nodes_executed = ["intent_detection", "response_generation"]

    turn_debug = TurnDebug(nodes_executed=nodes_executed, tool_calls=tool_calls)

    log.info(
        "chat turn done: intents=%s handover=%s clarification=%s",
        [i.intent for i in intent_debug],
        requires_handover,
        awaiting_clarification,
    )

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        intents=intent_debug,
        requires_handover=requires_handover,
        awaiting_clarification=awaiting_clarification,
        turn_debug=turn_debug,
    )


@router.get("/sessions")
async def get_sessions():
    return {"sessions": list_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, request: Request):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": session_id}}
    try:
        state_snapshot = graph.get_state(config)
        messages = [
            {"role": m.__class__.__name__, "content": m.content}
            for m in state_snapshot.values.get("messages", [])
        ]
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
