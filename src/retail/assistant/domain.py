from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from retail.domain.customer import ShopperProfile
from retail.domain.order import Order
from retail.recommendations.domain import Recommendation

Role = Literal["user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens_used: int = 0


class ConversationContext(BaseModel):
    session_id: str
    profile: ShopperProfile
    conversation_history: list[Message] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    basket: list[dict[str, object]] = Field(default_factory=list)


class AssistantResponse(BaseModel):
    message: str
    recommended_product_ids: list[str] = Field(default_factory=list)
    follow_up_question: str | None = None
    order: Order | None = None
    tokens_used: int = 0
