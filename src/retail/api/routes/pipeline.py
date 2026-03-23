from __future__ import annotations

import sqlite3

import polars as pl
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from retail.pipeline.pipeline import TransactionPipeline
from retail.recommendations.engine import KNNRecommendationEngine

router = APIRouter(tags=["pipeline"])


class PipelineRunResponse(BaseModel):
    status: str
    profiles_created: int
    message: str


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(request: Request) -> PipelineRunResponse:
    """Trigger the ETL batch pipeline."""
    try:
        db_path = request.app.state.db_path
        conn = sqlite3.connect(db_path)
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

        engine = KNNRecommendationEngine(catalogue=request.app.state.catalogue).fit(profiles)

        request.app.state.engine = engine
        request.app.state.profiles_by_id = {p.customer_id: p for p in profiles}

        return PipelineRunResponse(
            status="ok",
            profiles_created=len(profiles),
            message=f"Pipeline complete. {len(profiles)} profiles built and KNN refitted.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
