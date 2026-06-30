# CS Chatbot POC — Handover Document

**Last updated:** 2026-06-29
**Repo:** `noon/repos_ai/cs-chatbot-poc`
**Status:** Working prototype — ready for review and iteration

---

## What was built

A fully working local prototype of an AI-powered customer support chatbot using LangGraph + FastAPI + GPT. The goal was to validate the two-node agentic approach before committing to a production architecture.

Two sessions of work were done:
1. **Session 1** — Core agent: LangGraph pipeline, intent detection, response generation, mock tools, SOPs, FastAPI, 23 unit tests
2. **Session 2** — Demo UI: animated graph visualization, tool call inspector, 7 demo scenarios with auto-play

---

## Architecture

```
Customer Message
      │
      ▼
┌─────────────────────┐
│  Intent Detection    │  gpt-4o-mini (temperature=0)
│  Node                │  - Structured output: list of DetectedIntent
│                      │  - Extracts entities (order_id, product_id)
│                      │  - Checks required slots vs INTENT_REGISTRY
│                      │  - Sets clarification_question if slots missing
└─────────────────────┘
      │
  missing slots? ──yes──► Clarify node ──► AIMessage(question) ──► END
      │ no
      ▼
┌─────────────────────┐
│  Response Generation │  gpt-4o (temperature=0.3)
│  Node                │  - Calls mock tools per intent (orchestrated, not LLM tool-calling)
│                      │  - Retrieves SOP text per intent
│                      │  - Single synthesis call → final response
└─────────────────────┘
      │
      ▼
   AIMessage ──► END
```

**Multi-intent:** one message can produce multiple `IntentItem`s. Each is resolved independently; a single final LLM call synthesizes them into one coherent reply.

**Session memory:** `MemorySaver` checkpointer, keyed by `session_id` = `thread_id`. Multi-turn memory is free — no DB needed.

---

## File map

```
src/cschatbot/
├── config.py                   # pydantic-settings: OPENAI_API_KEY, INTENT_MODEL, RESPONSE_MODEL
│
├── models/
│   ├── enums.py                # IntentType (8 values), IntentStatus
│   ├── state.py                # GraphState (LangGraph schema), IntentItem
│   ├── tools.py                # Pydantic output models for each mock tool
│   └── api.py                  # ChatRequest, ChatResponse, TurnDebug, ToolCallDebug
│
├── intents/
│   └── taxonomy.py             # INTENT_REGISTRY: intent → {tools, sop_key, required_slots}
│
├── sops/
│   ├── content.py              # SOP_LIBRARY: 7 SOP texts
│   └── retrieval.py            # retrieve_sop(intent) → str  [TODO: swap for vector store]
│
├── tools/
│   ├── mocks.py                # 5 deterministic mock tools with seeded order/product data
│   └── registry.py             # TOOL_REGISTRY, call_tool(), get_tools_for_intent()
│
├── llm/
│   └── client.py               # get_llm(tier) factory — lru_cached ChatOpenAI instances
│
├── graph/
│   ├── builder.py              # build_graph() → compiled LangGraph with MemorySaver
│   ├── routing.py              # route_after_intent(): "clarify" | "respond"
│   └── nodes/
│       ├── intent_detection.py # Node 1: gpt-4o-mini structured output → IntentItem list
│       └── response_generation.py  # Node 2: tool calls + SOP + gpt-4o synthesis
│
├── api/
│   ├── app.py                  # FastAPI factory, lifespan (builds graph once), static mount
│   ├── routes.py               # POST /chat, GET /health, GET /demo/scenarios, GET /sessions/{id}
│   └── session.py              # In-memory session ID registry
│
└── static/
    └── index.html              # Self-contained demo UI (all CSS+JS inline, no CDN)
```

---

## Seeded demo data

### Orders (use these IDs in the UI)

| Order ID  | Status       | Items                          |
|-----------|-------------|--------------------------------|
| NXY-1001  | in_transit  | Samsung Galaxy S24, Phone Case  |
| NXY-2002  | delivered   | Sony WH-1000XM5 Headphones     |
| NXY-3003  | processing  | Nike Air Max 270, Adidas Socks |
| NXY-4004  | cancelled   | Apple AirPods Pro              |

### Refunds (only on delivered/cancelled orders)

| Order     | Status    | Amount   |
|-----------|-----------|----------|
| NXY-2002  | approved  | AED 450  |
| NXY-4004  | processed | AED 199  |

### Warranties

| Product ID       | Status              | Expiry        |
|-----------------|---------------------|---------------|
| PRD-A           | in warranty         | 2026-12-31    |
| PRD-B           | expired             | 2025-06-01    |
| PRD-GALAXY-S24  | in warranty         | 2027-03-15    |

---

## Running it

```bash
cd repos_ai/cs-chatbot-poc
cp .env.example .env      # add OPENAI_API_KEY=sk-...
make install              # uv sync --extra dev
make run                  # uvicorn on :8080

# Open browser:  http://localhost:8080
# API docs:      http://localhost:8080/docs
# Tests:         make test
```

---

## API contract

### POST /chat

```json
// Request
{ "message": "Where is order NXY-1001?", "session_id": null }

// Response
{
  "session_id": "uuid",
  "response": "Your order NXY-1001 is currently in transit…",
  "intents": [
    { "intent": "order_tracking", "status": "resolved",
      "entities": {"order_id": "NXY-1001"}, "missing_slots": [] }
  ],
  "requires_handover": false,
  "awaiting_clarification": false,
  "turn_debug": {
    "nodes_executed": ["intent_detection", "response_generation"],
    "tool_calls": [
      { "tool_name": "lookup_order", "inputs": {"order_id": "NXY-1001"},
        "output": {"order_id": "NXY-1001", "status": "in_transit", ...},
        "intent": "order_tracking" }
    ]
  }
}
```

Pass `session_id` from the previous response to continue a conversation. Omit (or pass `null`) to start a new session.

---

## Key design decisions made (and why)

| Decision | Choice | Rationale |
|---|---|---|
| Tool execution style | Orchestrated Python calls | Deterministic and testable for a POC; LLM tool-calling is an alternative noted in code |
| Multi-intent | List decomposition at detection, single synthesis call | One coherent reply; avoids stitching fragments |
| Clarification strategy | Ask once for ALL missing slots together | Better UX than multiple back-and-forths |
| SOP retrieval | Dict lookup (`sop_key` → text) | Fast for POC; hook left for vector store swap |
| Session memory | `MemorySaver` (in-process) | Zero setup; lost on restart — acceptable for POC |
| Intent model | gpt-4o-mini, temp=0 | Cheap, fast, structured output; classification doesn't need creativity |
| Response model | gpt-4o, temp=0.3 | Stronger reasoning for SOP grounding + synthesis |

---

## What's not done / next steps

These are the natural next iterations to discuss and work on:

### Short-term (POC validation)
- [ ] **Evaluate intent accuracy** — run the 7 demo scenarios and note where the model misclassifies or extracts wrong entities. Adjust the system prompt in `intent_detection.py`.
- [ ] **Add real Noon order IDs** — swap `tools/mocks.py` with calls to `mp-noon-order-api` to test with real data.
- [ ] **Tune clarification logic** — currently asks for ALL missing slots upfront; consider resolving resolvable intents first and asking for only the missing piece.
- [ ] **Add more intents** — payment queries, delivery address changes, account issues.

### Medium-term (productionise)
- [ ] **Persistent memory** — swap `MemorySaver` → `AsyncPostgresSaver` in `graph/builder.py`. Session state survives restarts and scales horizontally.
- [ ] **SOP vector retrieval** — replace `sops/retrieval.py` dict lookup with embedding search over a larger SOP library. Hook point is already marked with `# TODO`.
- [ ] **Real tool clients** — replace `tools/mocks.py` with HTTP clients to `mp-noon-order-api`, `mp-customer-api`, etc. Tool signatures and Pydantic output models stay the same.
- [ ] **Streaming responses** — FastAPI SSE + LangGraph `.astream_events()` for typewriter effect in the UI.
- [ ] **Auth** — JWT middleware on `/chat`; map `customer_id` from token into the graph state so tools can look up the right customer without the customer providing their own order IDs.
- [ ] **Human handover integration** — when `requires_handover=True`, push to a queue consumed by `mp-customer-support-api` (CARE Engine).

### Architecture decisions to make
- **LLM tool-calling vs. orchestrated calls** — current approach is orchestrated (predictable, cheap). LLM tool-calling (bind tools to gpt-4o, let the model decide) is more flexible for complex multi-step reasoning but less deterministic. Worth A/B testing on the accuracy eval.
- **Single graph vs. multi-graph** — current single graph handles all intents. Alternatively, route to per-intent subgraphs for more specialised handling (e.g., a dedicated returns flow with more steps).
- **Where does this live in prod?** — this POC is standalone. In production it would either be merged into `mp-noon-cs-agentic-ai` (the main Dialog agent repo) or become a new service consumed by `mp-noon-chat-api`.

---

## Codebase conventions

- **Python 3.11+**, managed with `uv`, `src/` layout
- `pydantic-settings` for config — all settings come from `.env` / env vars
- `ruff` for linting and formatting (`make lint` / `make format`)
- No comments on obvious code; comments only for non-obvious invariants
- Tests in `tests/` — no LLM calls in unit tests (mock or skip); all current tests run in ~0.1s

---

## Prompts (editable without code changes)

Both core prompts live as module-level constants in their node files:

- **Intent detection prompt:** `src/cschatbot/graph/nodes/intent_detection.py` — `SYSTEM_PROMPT`
- **Response synthesis prompt:** `src/cschatbot/graph/nodes/response_generation.py` — `SYNTHESIS_SYSTEM`

These are the primary levers for tuning agent behaviour.
