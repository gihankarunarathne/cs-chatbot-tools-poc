from pydantic import BaseModel, Field

from .enums import IntentType


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class IntentDebug(BaseModel):
    intent: IntentType
    status: str
    entities: dict[str, str]


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intents: list[IntentDebug] = Field(default_factory=list)
    requires_handover: bool = False
    awaiting_clarification: bool = False
