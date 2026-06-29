# CS Chatbot POC

Customer support chatbot prototype using **LangGraph** + **FastAPI** + **GPT**.

## Architecture

```
Customer Message
      │
      ▼
┌─────────────────────┐
│  Intent Detection    │  gpt-4o-mini — classifies intents, extracts entities,
│  Node                │  checks for missing required info
└─────────────────────┘
      │
  ┌───┴────────────┐
  │ missing info?  │
  └───┬────────────┘
      │ yes → ask clarifying question → END
      │ no
      ▼
┌─────────────────────┐
│  Response Generation │  gpt-4o — calls mock tools, retrieves SOPs,
│  Node                │  synthesizes final response
└─────────────────────┘
      │
      ▼
  Final Response
```

**Multi-intent support**: a single message like *"Where's order NXY-1001 and did my refund for NXY-2002 arrive?"* is decomposed into two intents, each resolved independently, then synthesized into one coherent reply.

## Seeded Demo Data

| Order ID  | Status       | Refund |
|-----------|-------------|--------|
| NXY-1001  | In transit  | None   |
| NXY-2002  | Delivered   | Approved (AED 450) |
| NXY-3003  | Processing  | None   |
| NXY-4004  | Cancelled   | Processed (AED 199) |

| Product ID       | Warranty        |
|-----------------|-----------------|
| PRD-A           | In warranty until 2026-12-31 |
| PRD-B           | Expired 2025-06-01 |
| PRD-GALAXY-S24  | In warranty until 2027-03-15 |

## Setup

```bash
# 1. Copy and fill in your OpenAI API key
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-...

# 2. Install dependencies (requires uv)
make install

# 3. Run the server
make run
# → http://localhost:8080
```

## API Usage

### Single intent — order tracking

```bash
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Where is my order NXY-1001?"}' | jq .
```

### Multi-intent — tracking + refund

```bash
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Where is order NXY-1001 and has my refund for NXY-2002 been processed?"}' | jq .
```

### Clarification flow (missing order ID)

```bash
# Turn 1 — bot asks for order ID
SESSION=$(curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to track my order"}' | jq -r .session_id)

# Turn 2 — provide it
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"It's NXY-3003\", \"session_id\": \"$SESSION\"}" | jq .
```

### Warranty claim

```bash
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to claim warranty on product PRD-A, it stopped working"}' | jq .
```

### Return request

```bash
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to return my order NXY-2002"}' | jq .
```

### View session history

```bash
curl -s http://localhost:8080/sessions/$SESSION | jq .
```

## Running Tests

```bash
make test
```

Tests cover: mock tool I/O contracts, SOP retrieval, multi-intent slot logic. No LLM calls in unit tests.

## Extending for Production

- **SOP retrieval**: swap `sops/retrieval.py` dict lookup for a vector store (e.g. pgvector, Pinecone)
- **Real tools**: replace `tools/mocks.py` with actual API clients
- **Persistence**: swap `MemorySaver` in `graph/builder.py` for `AsyncPostgresSaver`
- **Auth**: add JWT middleware to FastAPI
- **Models**: adjust `INTENT_MODEL` / `RESPONSE_MODEL` env vars
