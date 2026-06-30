from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from .enums import IntentStatus, IntentType


class IntentItem(BaseModel):
    intent: IntentType
    status: IntentStatus = IntentStatus.PENDING
    entities: dict[str, str] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    query_text: str = ""
    tool_results: dict[str, dict] = Field(default_factory=dict)


class GraphState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    intents: list[IntentItem] = Field(default_factory=list)
    clarification_question: str | None = None
    final_response: str | None = None
    requires_handover: bool = False
