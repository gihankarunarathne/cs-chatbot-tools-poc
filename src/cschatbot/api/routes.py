from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage

from ..models.api import ChatRequest, ChatResponse, IntentDebug
from .session import list_sessions, new_session_id, register_session

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    graph = request.app.state.graph

    session_id = body.session_id or new_session_id()
    register_session(session_id)

    config = {"configurable": {"thread_id": session_id}}
    graph_input = {"messages": [HumanMessage(content=body.message)]}

    final_state = await graph.ainvoke(graph_input, config=config)

    response_text = final_state.get("final_response") or "I'm sorry, I couldn't process your request."
    intents = final_state.get("intents", [])
    requires_handover = final_state.get("requires_handover", False)
    awaiting_clarification = bool(final_state.get("clarification_question"))

    intent_debug = [
        IntentDebug(intent=i.intent, status=i.status, entities=i.entities)
        for i in intents
    ]

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        intents=intent_debug,
        requires_handover=requires_handover,
        awaiting_clarification=awaiting_clarification,
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
