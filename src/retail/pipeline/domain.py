from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Channel = Literal["online", "instore"]
SegmentLabel = Literal["champions", "loyal", "at_risk", "lost"]


class Transaction(BaseModel):
    """A single retail transaction."""

    transaction_id: str
    customer_id: str
    amount_gbp: float
    category: str
    timestamp: datetime
    channel: Channel = "instore"
    is_return: bool = False

    @field_validator("amount_gbp")
    @classmethod
    def amount_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"amount_gbp must be >= 0, got {v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_not_be_future(cls, v: datetime) -> datetime:
        if v > datetime.now():
            raise ValueError(f"timestamp must not be in the future, got {v}")
        return v

    model_config = {"frozen": True}


class RFMSegment(BaseModel):
    """RFM profile for a single customer."""

    customer_id: str
    recency_days: int = Field(ge=0)
    frequency_count: int = Field(ge=0)
    monetary_gbp: float = Field(ge=0)
    segment: SegmentLabel = "at_risk"


class TransactionBatch(BaseModel):
    """A validated batch of transactions ready for processing."""

    transactions: list[Transaction] = Field(default_factory=list)
    source: str = "unknown"

    @property
    def count(self) -> int:
        return len(self.transactions)
