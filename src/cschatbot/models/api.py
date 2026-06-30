from pydantic import BaseModel, Field

from .enums import IntentType


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class IntentDebug(BaseModel):
    intent: IntentType
    status: str
    entities: dict[str, str]
    missing_slots: list[str] = Field(default_factory=list)


class ToolCallDebug(BaseModel):
    tool_name: str
    inputs: dict
    output: dict
    intent: str


class TurnDebug(BaseModel):
    nodes_executed: list[str]
    tool_calls: list[ToolCallDebug] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intents: list[IntentDebug] = Field(default_factory=list)
    requires_handover: bool = False
    awaiting_clarification: bool = False
    turn_debug: TurnDebug | None = None
