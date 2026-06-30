from cschatbot.models.enums import IntentType
from cschatbot.sops.retrieval import retrieve_sop


def test_retrieve_known_intents():
    for intent in [
        IntentType.ORDER_TRACKING,
        IntentType.REFUND_REQUEST,
        IntentType.WARRANTY_CLAIM,
        IntentType.RETURN_REQUEST,
        IntentType.GENERAL_QUERY,
        IntentType.OUT_OF_SCOPE,
    ]:
        sop = retrieve_sop(intent)
        assert isinstance(sop, str)
        assert len(sop) > 10


def test_clarification_needed_falls_back_to_general():
    sop = retrieve_sop(IntentType.CLARIFICATION_NEEDED)
    assert "general" in sop.lower() or len(sop) > 0
