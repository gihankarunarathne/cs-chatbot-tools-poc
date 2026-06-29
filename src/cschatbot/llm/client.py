from functools import lru_cache
from typing import Literal

from langchain_openai import ChatOpenAI

from ..config import settings

ModelTier = Literal["intent", "response"]


@lru_cache(maxsize=4)
def get_llm(tier: ModelTier, temperature: float = 0.0) -> ChatOpenAI:
    model = settings.intent_model if tier == "intent" else settings.response_model
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.openai_api_key,
    )
