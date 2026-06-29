"""
Simulation scenarios — each defines a customer persona and an opening message.

Personas reference the seeded mock data so the bot can actually resolve them:
  Orders:   NXY-1001 (in_transit), NXY-2002 (delivered), NXY-3003 (processing), NXY-4004 (cancelled)
  Refunds:  NXY-2002 (approved, 450 AED), NXY-4004 (processed, 199 AED)
  Warranty: PRD-A (in warranty), PRD-B (expired), PRD-GALAXY-S24 (in warranty)
"""

SCENARIOS: list[dict] = [
    # ── Single-intent, info provided upfront ─────────────────────────────────
    {
        "id": "SIM-01",
        "title": "Track in-transit order",
        "persona": (
            "You ordered a Samsung Galaxy S24 (order NXY-1001) 3 days ago. "
            "It hasn't arrived yet and you are getting impatient. "
            "You know your order ID. Your goal: find out when it will arrive."
        ),
        "opening_message": "Hi, I placed order NXY-1001 three days ago and it still hasn't arrived. Where is it?",
        "max_turns": 4,
    },
    {
        "id": "SIM-02",
        "title": "Refund status check",
        "persona": (
            "You returned your Sony WH-1000XM5 Headphones (order NXY-2002) a week ago "
            "and are waiting for your 450 AED refund. You have the order ID ready. "
            "Your goal: confirm the refund has been approved and find out when it will appear."
        ),
        "opening_message": "I returned my headphones under order NXY-2002. Has my refund been processed yet?",
        "max_turns": 4,
    },
    {
        "id": "SIM-03",
        "title": "Warranty claim",
        "persona": (
            "Your product (product ID PRD-A) stopped charging two days ago. "
            "You believe it's a manufacturing defect and want to file a warranty claim. "
            "Your goal: confirm the product is under warranty and start the claim process."
        ),
        "opening_message": "My product PRD-A has stopped charging completely. I think it's a manufacturing defect and I want to claim warranty.",
        "max_turns": 5,
    },
    # ── Clarification required (starts without ID) ────────────────────────────
    {
        "id": "SIM-04",
        "title": "Track order — provides ID only when asked",
        "persona": (
            "You ordered Nike Air Max 270 shoes (order NXY-3003) and want to know the status. "
            "You forget to include your order number in the first message, but you know it: NXY-3003. "
            "When the bot asks for your order ID, provide it. "
            "Your goal: find out when your order will ship."
        ),
        "opening_message": "Hey can you tell me where my order is? I ordered some shoes.",
        "max_turns": 6,
    },
    {
        "id": "SIM-05",
        "title": "Return request — provides ID only when asked",
        "persona": (
            "You received Sony WH-1000XM5 Headphones (order NXY-2002) but they don't fit comfortably. "
            "You want to return them. You forget to mention the order ID at first. "
            "When asked, you provide NXY-2002. "
            "Your goal: initiate the return and learn the next steps."
        ),
        "opening_message": "I want to return some headphones I bought, they don't fit right.",
        "max_turns": 6,
    },
    # ── Multi-intent in one message ───────────────────────────────────────────
    {
        "id": "SIM-06",
        "title": "Track order + check refund in one message",
        "persona": (
            "You have two active issues: "
            "1) Your order NXY-1001 (Samsung Galaxy S24) is in transit and you want the ETA. "
            "2) Your refund for order NXY-2002 (headphones) was approved and you want to know when it will arrive in your account. "
            "Ask about both in a single message upfront."
        ),
        "opening_message": "Quick questions — where is my order NXY-1001, and also when will my refund for NXY-2002 hit my account?",
        "max_turns": 4,
    },
    # ── Human escalation ──────────────────────────────────────────────────────
    {
        "id": "SIM-07",
        "title": "Escalation — customer demands human immediately",
        "persona": (
            "You have been waiting 3 weeks for a refund on a cancelled order and nothing has happened. "
            "You are furious and do not want to talk to a bot. You want a human manager immediately. "
            "You are not interested in bot answers and will keep demanding a human. "
            "Your goal: get escalated to a human agent."
        ),
        "opening_message": "I've been waiting THREE WEEKS for my refund. This is absolutely unacceptable. I want to speak to a manager NOW.",
        "max_turns": 4,
    },
    # ── Expired warranty edge case ────────────────────────────────────────────
    {
        "id": "SIM-08",
        "title": "Expired warranty — customer pushes back",
        "persona": (
            "Your product (PRD-B) is broken but you discover the warranty has expired. "
            "You are disappointed and will push back, asking if there are any exceptions or alternative options. "
            "Your goal: understand your options even though the warranty is expired."
        ),
        "opening_message": "My product PRD-B is completely broken. I want to make a warranty claim.",
        "max_turns": 6,
    },
]

SCENARIOS_BY_ID: dict[str, dict] = {s["id"]: s for s in SCENARIOS}
