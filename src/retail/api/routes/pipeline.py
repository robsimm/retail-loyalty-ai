from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["pipeline"])


class PipelineRunResponse(BaseModel):
    status: str
    profiles_created: int
    message: str


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline() -> PipelineRunResponse:
    """Trigger the ETL batch pipeline."""
    try:
        # In production, load from DB and run real pipeline
        return PipelineRunResponse(
            status="ok",
            profiles_created=0,
            message="Pipeline endpoint ready. Seed data first via /seed-data skill.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
