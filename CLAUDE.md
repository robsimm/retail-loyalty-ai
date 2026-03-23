# Retail Loyalty AI

## What This Is
Three-component Python system: club-card ETL pipeline, KNN recommendations,
and Claude-powered shopping assistant. TDD throughout. See README for full docs.

## Architecture
- src/retail/pipeline/    → Polars ETL, RFM segmentation
- src/retail/recommendations/ → scikit-learn KNN engine
- src/retail/assistant/   → Claude haiku-4-5 agent with tool_use
- src/retail/api/         → FastAPI + WebSocket + minimal HTML UI
- src/retail/domain/      → Shared Pydantic v2 models

## Key Commands
- Run all tests:       pytest
- Run unit tests only: pytest tests/unit -m unit
- Start API server:    uvicorn src.retail.api.main:app --reload
- Seed test data:      python -m scripts.seed_data
- Run pipeline:        python -m scripts.run_pipeline

## Code Patterns
- ALL domain models use Pydantic v2 with validation
- Business logic lives in pure functions first, classes second
- Pipeline uses fluent/builder pattern: .load().validate().transform()
- Assistant tools are defined in assistant/tools.py as JSON schema dicts
- No direct DB calls outside of repository functions
- SQLite for dev, PostgreSQL for prod (config via DATABASE_URL env var)

## Testing Philosophy
- Write the failing test FIRST (TDD)
- Unit tests: pure functions, no I/O, no mocks unless boundary
- Integration tests: real SQLite (in-memory), no network calls
- LLM tests: always mock the Claude client; use pre-recorded responses
- Test naming: test_<scenario>_<given_context>_<expected_outcome>

## Scale Notes
- Polars handles 10M+ rows single-machine; PySpark for larger
- scikit-learn KNN up to ~5M profiles; swap NearestNeighbors for FAISS beyond
- SQLite → PostgreSQL: change DATABASE_URL, no code changes needed
- In-memory cache → Redis: implement CachePort protocol, swap adapter

## Claude API
- Model: claude-haiku-4-5-20251001 (fast, cheap for chat)
- Upgrade to claude-sonnet-4-6 for more complex reasoning
- All Claude calls in assistant/assistant.py only
- Prompts built in assistant/prompts.py (pure, testable functions)
- Tool handlers in assistant/tools.py
- Never call Claude from pipeline or recommendations modules

## Security
- NEVER write API keys in code or suggest doing so
- All secrets via environment variables only
- .env file is gitignored - never commit it
