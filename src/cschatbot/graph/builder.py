from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ..models.state import GraphState
from .nodes.intent_detection import intent_detection_node
from .nodes.response_generation import response_generation_node
from .routing import route_after_intent


def _clarify_node(state: GraphState) -> dict:
    """Emit the clarification question as an AI message and end the turn."""
    question = state.clarification_question or "Could you provide more details?"
    return {"messages": [AIMessage(content=question)], "final_response": question}


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("intent_detection", intent_detection_node)
    g.add_node("response_generation", response_generation_node)
    g.add_node("clarify", _clarify_node)

    g.add_edge(START, "intent_detection")
    g.add_conditional_edges(
        "intent_detection",
        route_after_intent,
        {"clarify": "clarify", "respond": "response_generation"},
    )
    g.add_edge("clarify", END)
    g.add_edge("response_generation", END)

    return g.compile(checkpointer=MemorySaver())
