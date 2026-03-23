from __future__ import annotations

from datetime import date
from typing import Self

import polars as pl

from retail.domain.customer import ShopperProfile
from retail.pipeline.rfm import build_rfm_profiles
from retail.pipeline.transforms import deduplicate_transactions


class TransactionPipeline:
    """
    Fluent pipeline for transforming raw transaction CSVs into ShopperProfiles.

    Usage:
        profiles = (
            TransactionPipeline()
            .load("data/transactions.csv")
            .validate()
            .transform()
            .aggregate_rfm(as_of_date=date.today())
            .to_profiles()
        )
    """

    def __init__(self) -> None:
        self._df: pl.DataFrame | None = None
        self._as_of_date: date = date.today()

    def load(self, path: str) -> Self:
        self._df = pl.read_csv(path, try_parse_dates=True)
        return self

    def load_df(self, df: pl.DataFrame) -> Self:
        self._df = df
        return self

    def validate(self) -> Self:
        assert self._df is not None, "Call .load() first"
        required = {"transaction_id", "customer_id", "amount_gbp", "timestamp"}
        missing = required - set(self._df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return self

    def transform(self) -> Self:
        assert self._df is not None
        self._df = deduplicate_transactions(self._df)
        return self

    def aggregate_rfm(self, as_of_date: date | None = None) -> Self:
        assert self._df is not None
        if as_of_date:
            self._as_of_date = as_of_date
        self._df = build_rfm_profiles(self._df, self._as_of_date)
        return self

    def to_profiles(self) -> list[ShopperProfile]:
        assert self._df is not None
        profiles: list[ShopperProfile] = []
        for row in self._df.iter_rows(named=True):
            features = [
                float(row.get("recency_days_norm", 0.0)),
                float(row.get("frequency_count_norm", 0.0)),
                float(row.get("monetary_gbp_norm", 0.0)),
            ]
            profiles.append(
                ShopperProfile(
                    customer_id=str(row["customer_id"]),
                    age_bracket="35-44",
                    preferred_categories=[],
                    channel_preference="both",
                    normalized_features=features,
                    rfm_segment=str(row.get("segment", "at_risk")),  # type: ignore[arg-type]
                )
            )
        return profiles

    def result_df(self) -> pl.DataFrame:
        assert self._df is not None
        return self._df
