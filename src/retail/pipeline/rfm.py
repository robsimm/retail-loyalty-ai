from __future__ import annotations

from datetime import date

import polars as pl

from retail.pipeline.transforms import calculate_rfm, normalize_features, segment_by_rfm


def build_rfm_profiles(transactions_df: pl.DataFrame, as_of_date: date | None = None) -> pl.DataFrame:
    """
    Full RFM pipeline: transactions → normalised, segmented RFM profiles.

    Returns a DataFrame with columns:
    customer_id, recency_days, frequency_count, monetary_gbp,
    recency_days_norm, frequency_count_norm, monetary_gbp_norm, segment
    """
    if as_of_date is None:
        as_of_date = date.today()

    rfm = calculate_rfm(transactions_df, as_of_date)
    rfm = normalize_features(rfm, ["recency_days", "frequency_count", "monetary_gbp"])
    rfm = segment_by_rfm(rfm)
    return rfm
