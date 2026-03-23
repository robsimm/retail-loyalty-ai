from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    """A product in the retail catalogue."""

    product_id: str
    name: str
    category: str
    price_gbp: float = Field(gt=0)
    is_high_consideration: bool = False
    available_online: bool = True
    available_instore: bool = True

    model_config = {"frozen": True}


class Catalogue(BaseModel):
    """The full product catalogue."""

    products: list[Product] = Field(default_factory=list)

    def find_by_id(self, product_id: str) -> Product | None:
        return next((p for p in self.products if p.product_id == product_id), None)

    def search(self, query: str = "", category: str = "", limit: int = 10) -> list[Product]:
        results = self.products
        if category:
            results = [p for p in results if p.category.lower() == category.lower()]
        if query:
            q = query.lower()
            results = [p for p in results if q in p.name.lower() or q in p.category.lower()]
        return results[:limit]
