from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AgeBracket = Literal["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
ChannelPreference = Literal["online", "instore", "both"]
RFMSegmentLabel = Literal["champions", "loyal", "at_risk", "lost"]


class ShopperProfile(BaseModel):
    """Enriched customer profile produced by the ETL pipeline."""

    customer_id: str
    age_bracket: AgeBracket
    preferred_categories: list[str] = Field(default_factory=list)
    channel_preference: ChannelPreference = "both"
    normalized_features: list[float] = Field(default_factory=list)
    rfm_segment: RFMSegmentLabel = "at_risk"

    model_config = {"frozen": True}


class ClubCardAccount(BaseModel):
    """Raw club-card account from the source system."""

    customer_id: str
    age_bracket: AgeBracket
    signup_date: str
    channel_preference: ChannelPreference = "both"
    is_active: bool = True
