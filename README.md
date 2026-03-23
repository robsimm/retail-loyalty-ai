# retail-loyalty-ai

Retail personalization POC: club-card ETL pipeline, KNN product recommendations, and a Claude-powered shopping assistant — built through pair-programming with [Claude Code](https://claude.ai/claude-code).

---

## Features

- RFM segmentation of customer transaction history using Polars
- KNN collaborative filtering to generate personalized product recommendations
- Conversational shopping assistant (Claude Haiku) with tool use for search, basket management, and order placement
- FastAPI REST API + WebSocket chat endpoint
- Minimal browser UI to interact with the system end-to-end
- 67 tests across unit, integration, and e2e layers

---

## Tech Stack

| | |
|---|---|
| ETL pipeline | [Polars](https://pola.rs) |
| Recommendations | [scikit-learn](https://scikit-learn.org) NearestNeighbors |
| Assistant | [Anthropic Claude Haiku](https://www.anthropic.com) via tool use |
| API | [FastAPI](https://fastapi.tiangolo.com) + WebSocket |
| Data validation | [Pydantic v2](https://docs.pydantic.dev) |
| Storage | SQLite (dev), PostgreSQL-ready via `DATABASE_URL` |

---

## Getting Started

**Requirements:** Python 3.11+, an [Anthropic API key](https://console.anthropic.com)

```bash
git clone <this-repo>
cd retail-loyalty-ai

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

Start the server:

```bash
uvicorn src.retail.api.main:app --reload
```

On first run the server seeds a SQLite database with 1,000 synthetic customers, 200 products, and realistic transaction history. Open `http://localhost:8000` to use the chat UI. API docs are at `http://localhost:8000/docs`.

---

## Usage

Select a customer from the dropdown (e.g. `CUS_00000001`) and chat:

```
> What do you recommend for me today?
> Tell me more about the first one
> Add it to my basket
> What delivery slots are available?
> Book tomorrow morning
```

The assistant calls the appropriate internal tool at each step — KNN recommendations, catalogue search, basket management, order placement — and responds in natural language.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/customers/{id}/profile` | RFM segment and preferred categories |
| `GET` | `/api/v1/customers/{id}/recommendations` | KNN-ranked product list |
| `POST` | `/api/v1/chat/start?customer_id={id}` | Create a chat session |
| `WS` | `/api/v1/chat/{session_id}` | WebSocket chat stream |
| `POST` | `/api/v1/pipeline/run` | Re-run ETL and refit KNN |

---

## How It Works

**Pipeline** — Raw transactions are loaded into Polars, deduplicated, and aggregated into RFM (recency, frequency, monetary) features. Customers are scored and assigned to one of four segments: `champions`, `loyal`, `at_risk`, `lost`.

**Recommendations** — RFM feature vectors are normalized and indexed with scikit-learn `NearestNeighbors`. For a given customer, the engine finds similar customers, scores catalogue products by category affinity across that neighbour group, and returns a ranked list.

**Assistant** — At session start, the customer's `ShopperProfile` and their top-5 recommendations are loaded into a `ConversationContext`. Claude Haiku receives a system prompt with this context and a set of tools it can call: `get_recommendations`, `search_catalogue`, `add_to_basket`, `check_delivery_slots`, `place_order`. The WebSocket handler runs each `chat()` call in a thread pool so it doesn't block the event loop.

**Startup** — The FastAPI lifespan handler seeds the DB if missing, runs the full pipeline, fits the KNN engine, and caches the results in `app.state` so every request is fast.

---

## Project Structure

```
src/retail/
├── domain/           # Shared Pydantic models (ShopperProfile, Product, Order)
├── pipeline/         # Polars ETL: load → validate → transform → RFM → profiles
├── recommendations/  # KNN engine: fit(profiles), predict(customer_id)
├── assistant/        # Claude agent: prompts, tools, tool dispatch, conversation context
├── api/              # FastAPI app, routes, WebSocket chat handler
└── data/             # Synthetic data seeder

tests/
├── unit/             # Pure functions, no I/O
├── integration/      # Real SQLite, mocked Claude client
└── e2e/              # Full system smoke tests
```

---

## Running Tests

```bash
pytest                    # all tests with coverage report
pytest tests/unit         # unit only
pytest tests/integration  # integration only
```

The Claude client is always mocked in tests — no API calls, deterministic responses.

---

## Scaling

Each layer can be upgraded independently:

| Current | Upgrade path |
|---|---|
| SQLite | Set `DATABASE_URL` to a Postgres connection string |
| Polars single-machine | PySpark for 10M+ row datasets |
| scikit-learn KNN | FAISS for millions of profiles |
| In-memory sessions | Implement `SessionPort` and swap in Redis |
| Claude Haiku | Change `MODEL` in `assistant.py` to Sonnet or Opus |

---

## About This Project

This codebase was built as a pair-programming exercise with **Claude Code**. The development process: define requirements and architecture decisions as a human, then implement each layer in conversation with the AI — writing tests first, iterating on the design, and using Claude's feedback to catch edge cases. The result is a complete, tested stack built significantly faster than working alone.

If you're evaluating Claude Code for engineering work, this repo is a realistic example of what that workflow produces.
