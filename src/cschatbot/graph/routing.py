from ..models.state import GraphState


def route_after_intent(state: GraphState) -> str:
    # Handover takes priority — response node handles out_of_scope intents directly
    if state.requires_handover:
        return "respond"
    if state.clarification_question:
        return "clarify"
    return "respond"
