from ..models.state import GraphState


def route_after_intent(state: GraphState) -> str:
    if state.clarification_question:
        return "clarify"
    return "respond"
