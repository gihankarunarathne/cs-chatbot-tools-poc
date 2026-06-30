"""API-level integration tests, with the LLM mocked out so they run offline/deterministically."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from cschatbot.api.app import create_app
from cschatbot.graph.nodes.intent_detection import DetectedIntent, IntentDetectionResult
from cschatbot.models.enums import IntentType


class _FakeStructuredLLM:
    def __init__(self, result):
        self._result = result

    def invoke(self, messages):
        return self._result


class _FakeIntentLLM:
    """Stands in for get_llm("intent"); with_structured_output(...) returns the canned result."""

    def __init__(self, result: IntentDetectionResult):
        self._result = result

    def with_structured_output(self, schema):
        return _FakeStructuredLLM(self._result)


class _FakeResponseLLM:
    """Stands in for get_llm("response", ...); .invoke(...) returns a canned AIMessage."""

    def __init__(self, text: str):
        self._text = text

    def invoke(self, messages):
        return AIMessage(content=self._text)


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_chat_single_intent_order_tracking(client):
    intent_result = IntentDetectionResult(
        intents=[
            DetectedIntent(
                intent=IntentType.ORDER_TRACKING,
                order_id="NXY-1001",
                query_text="Where is my order NXY-1001?",
            )
        ]
    )

    with (
        patch(
            "cschatbot.graph.nodes.intent_detection.get_llm",
            return_value=_FakeIntentLLM(intent_result),
        ),
        patch(
            "cschatbot.graph.nodes.response_generation.get_llm",
            return_value=_FakeResponseLLM("Your order NXY-1001 is on its way!"),
        ),
    ):
        resp = client.post("/chat", json={"message": "Where is my order NXY-1001?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"]
    assert body["response"] == "Your order NXY-1001 is on its way!"
    assert body["requires_handover"] is False
    assert body["awaiting_clarification"] is False
    assert len(body["intents"]) == 1
    assert body["intents"][0]["intent"] == "order_tracking"
    assert body["intents"][0]["status"] == "resolved"


def test_chat_missing_slot_triggers_clarification(client):
    intent_result = IntentDetectionResult(
        intents=[
            DetectedIntent(
                intent=IntentType.ORDER_TRACKING,
                query_text="Where is my order?",
            )
        ]
    )

    with patch(
        "cschatbot.graph.nodes.intent_detection.get_llm",
        return_value=_FakeIntentLLM(intent_result),
    ):
        resp = client.post("/chat", json={"message": "Where is my order?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["awaiting_clarification"] is True
    assert body["intents"][0]["status"] == "needs_info"
    assert "order id" in body["response"].lower() or "order ID" in body["response"]


def test_chat_out_of_scope_sets_handover(client):
    intent_result = IntentDetectionResult(
        intents=[
            DetectedIntent(
                intent=IntentType.OUT_OF_SCOPE,
                query_text="I want to speak to a manager",
            )
        ]
    )

    with (
        patch(
            "cschatbot.graph.nodes.intent_detection.get_llm",
            return_value=_FakeIntentLLM(intent_result),
        ),
        patch(
            "cschatbot.graph.nodes.response_generation.get_llm",
            return_value=_FakeResponseLLM("A human agent will follow up shortly."),
        ),
    ):
        resp = client.post("/chat", json={"message": "I want to speak to a manager"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["requires_handover"] is True
    assert body["awaiting_clarification"] is False


def test_health_endpoint_reports_config(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["openai_configured"] is True


def test_chat_session_persists_across_turns(client):
    intent_result = IntentDetectionResult(
        intents=[
            DetectedIntent(
                intent=IntentType.ORDER_TRACKING,
                order_id="NXY-1001",
                query_text="Where is my order NXY-1001?",
            )
        ]
    )

    with (
        patch(
            "cschatbot.graph.nodes.intent_detection.get_llm",
            return_value=_FakeIntentLLM(intent_result),
        ),
        patch(
            "cschatbot.graph.nodes.response_generation.get_llm",
            return_value=_FakeResponseLLM("Your order is on its way!"),
        ),
    ):
        first = client.post("/chat", json={"message": "Where is my order NXY-1001?"})
        session_id = first.json()["session_id"]

        second = client.post(
            "/chat", json={"message": "Thanks, when exactly?", "session_id": session_id}
        )

    assert second.json()["session_id"] == session_id
