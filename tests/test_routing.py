from cschatbot.graph.routing import route_after_intent
from cschatbot.models.state import GraphState


def test_routes_to_clarify_when_question_pending():
    state = GraphState(clarification_question="What's your order ID?")
    assert route_after_intent(state) == "clarify"


def test_routes_to_respond_when_no_clarification_needed():
    state = GraphState()
    assert route_after_intent(state) == "respond"


def test_handover_takes_priority_over_clarification():
    state = GraphState(
        requires_handover=True,
        clarification_question="What's your order ID?",
    )
    assert route_after_intent(state) == "respond"


def test_handover_without_clarification_routes_to_respond():
    state = GraphState(requires_handover=True)
    assert route_after_intent(state) == "respond"
