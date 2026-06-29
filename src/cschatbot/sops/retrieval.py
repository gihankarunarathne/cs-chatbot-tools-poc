from ..intents.taxonomy import INTENT_REGISTRY
from ..models.enums import IntentType
from .content import SOP_LIBRARY


def retrieve_sop(intent: IntentType) -> str:
    # TODO: swap for embedding-based retrieval in production
    key = INTENT_REGISTRY.get(intent, {}).get("sop_key", "general")
    return SOP_LIBRARY.get(key, SOP_LIBRARY["general"])
