from __future__ import annotations

import random
from datetime import datetime, timedelta

import pytest
import polars as pl

from retail.domain.customer import ShopperProfile
from retail.domain.order import DeliverySlot, Order, OrderItem
from retail.domain.product import Catalogue, Product
from retail.pipeline.domain import Transaction


def make_transaction(**kwargs) -> Transaction:  # type: ignore[return]
    defaults = dict(
        transaction_id="TX_001",
        customer_id="CUS_001",
        amount_gbp=10.0,
        category="grocery",
        timestamp=datetime.now() - timedelta(days=1),
        channel="instore",
        is_return=False,
    )
    defaults.update(kwargs)
    return Transaction(**defaults)


def make_profile(**kwargs) -> ShopperProfile:  # type: ignore[return]
    defaults = dict(
        customer_id="CUS_001",
        age_bracket="35-44",
        preferred_categories=["grocery", "dairy"],
        channel_preference="both",
        normalized_features=[0.2, 0.8, 0.6],
        rfm_segment="loyal",
    )
    defaults.update(kwargs)
    return ShopperProfile(**defaults)


def make_product(**kwargs) -> Product:  # type: ignore[return]
    defaults = dict(
        product_id="PRD_001",
        name="Organic Milk",
        category="dairy",
        price_gbp=1.50,
        is_high_consideration=False,
        available_online=True,
        available_instore=True,
    )
    defaults.update(kwargs)
    return Product(**defaults)


def make_catalogue(n: int = 20) -> Catalogue:
    categories = ["grocery", "dairy", "bakery", "produce", "meat"]
    products = [
        make_product(
            product_id=f"PRD_{i:03d}",
            name=f"Product {i}",
            category=categories[i % len(categories)],
            price_gbp=round(1.0 + i * 0.5, 2),
            is_high_consideration=(i % 5 == 0),
        )
        for i in range(1, n + 1)
    ]
    return Catalogue(products=products)


@pytest.fixture
def sample_transaction() -> Transaction:
    return make_transaction()


@pytest.fixture
def sample_profile() -> ShopperProfile:
    return make_profile()


@pytest.fixture
def sample_catalogue() -> Catalogue:
    return make_catalogue()


@pytest.fixture
def sample_transactions_df() -> pl.DataFrame:
    rows = []
    now = datetime.now()
    for i in range(50):
        rows.append({
            "transaction_id": f"TX_{i:04d}",
            "customer_id": f"CUS_{(i % 5) + 1:03d}",
            "amount_gbp": 10.0 + i,
            "category": "grocery",
            "timestamp": (now - timedelta(days=i % 30)).isoformat(),
            "channel": "instore",
            "is_return": False,
        })
    return pl.DataFrame(rows)
