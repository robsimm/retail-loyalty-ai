from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from retail.api.routes import chat, pipeline, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: initialise DB, load models, etc.
    yield
    # Shutdown: cleanup


def create_app() -> FastAPI:
    app = FastAPI(
        title="Retail Loyalty AI",
        description="Club-card ETL, KNN recommendations, and conversational shopping assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(pipeline.router, prefix="/api/v1")
    app.include_router(recommendations.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")

    import pathlib
    static_path = pathlib.Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

    return app


app = create_app()
