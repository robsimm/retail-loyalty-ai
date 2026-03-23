from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OrderStatus = Literal["pending", "confirmed", "dispatched", "delivered", "cancelled"]


class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int = Field(ge=1)
    unit_price_gbp: float = Field(gt=0)

    @property
    def line_total_gbp(self) -> float:
        return self.quantity * self.unit_price_gbp


class DeliverySlot(BaseModel):
    slot_id: str
    date: str
    time_window: str
    available: bool = True


class Order(BaseModel):
    order_id: str
    customer_id: str
    items: list[OrderItem] = Field(default_factory=list)
    delivery_slot: DeliverySlot | None = None
    status: OrderStatus = "pending"

    @property
    def total_gbp(self) -> float:
        return sum(item.line_total_gbp for item in self.items)
