from __future__ import annotations

import os
import sqlite3
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import polars as pl
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from retail.api.routes import chat, pipeline, recommendations
from retail.data.seed import seed_database
from retail.domain.product import Catalogue, Product
from retail.pipeline.pipeline import TransactionPipeline
from retail.recommendations.engine import KNNRecommendationEngine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./retail.db")
    db_path = db_url.replace("sqlite:///./", "").replace("sqlite:///", "")

    if not os.path.exists(db_path):
        seed_database(db_path)

    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        "SELECT product_id, name, category, price_gbp, "
        "is_high_consideration, available_online, available_instore FROM products"
    ).fetchall()
    catalogue = Catalogue(products=[
        Product(
            product_id=r[0], name=r[1], category=r[2], price_gbp=r[3],
            is_high_consideration=bool(r[4]),
            available_online=bool(r[5]),
            available_instore=bool(r[6]),
        )
        for r in rows
    ])

    tx_rows = conn.execute(
        "SELECT transaction_id, customer_id, amount_gbp, category, "
        "timestamp, channel, is_return FROM transactions"
    ).fetchall()
    conn.close()

    df = pl.DataFrame(
        tx_rows,
        schema={
            "transaction_id": pl.String, "customer_id": pl.String,
            "amount_gbp": pl.Float64, "category": pl.String,
            "timestamp": pl.String, "channel": pl.String,
            "is_return": pl.Boolean,
        },
        orient="row",
    )
    df = df.with_columns(pl.col("timestamp").str.to_datetime())

    profiles = (
        TransactionPipeline()
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm()
        .to_profiles()
    )

    engine = KNNRecommendationEngine(catalogue=catalogue).fit(profiles)

    app.state.db_path = db_path
    app.state.catalogue = catalogue
    app.state.engine = engine
    app.state.profiles_by_id = {p.customer_id: p for p in profiles}
    app.state.sessions = {}

    yield


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
