from __future__ import annotations

from datetime import date

import polars as pl


def deduplicate_transactions(df: pl.DataFrame) -> pl.DataFrame:
    """Remove duplicate transaction_id rows, keeping first occurrence."""
    return df.unique(subset=["transaction_id"], keep="first", maintain_order=True)


def filter_returns(df: pl.DataFrame) -> pl.DataFrame:
    """Remove return transactions for frequency/monetary calculations."""
    return df.filter(pl.col("is_return") == False)  # noqa: E712


def calculate_rfm(df: pl.DataFrame, as_of_date: date) -> pl.DataFrame:
    """
    Aggregate transaction rows into one RFM row per customer.

    Recency  = days since last non-return purchase
    Frequency = count of non-return transactions
    Monetary  = sum of amount_gbp for non-return transactions
    """
    non_returns = filter_returns(df)
    as_of = pl.lit(as_of_date)

    rfm = non_returns.group_by("customer_id").agg(
        [
            (
                (as_of - pl.col("timestamp").cast(pl.Date).max()).dt.total_days()
            ).alias("recency_days"),
            pl.col("transaction_id").count().alias("frequency_count"),
            pl.col("amount_gbp").sum().alias("monetary_gbp"),
        ]
    )
    return rfm


def normalize_features(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Min-max normalise the specified numeric columns to [0, 1]."""
    for col in columns:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_max == col_min:
            df = df.with_columns(pl.lit(0.0).alias(f"{col}_norm"))
        else:
            df = df.with_columns(
                ((pl.col(col) - col_min) / (col_max - col_min)).alias(f"{col}_norm")
            )
    return df


def segment_by_rfm(df: pl.DataFrame) -> pl.DataFrame:
    """
    Assign segment labels based on RFM percentile scores.

    champions  = high frequency + low recency + high monetary
    loyal      = high frequency or monetary (not both champion-level)
    at_risk    = medium scores
    lost       = low frequency + high recency
    """
    df = df.with_columns(
        [
            pl.col("recency_days").rank(method="average").alias("recency_rank"),
            pl.col("frequency_count").rank(method="average").alias("frequency_rank"),
            pl.col("monetary_gbp").rank(method="average").alias("monetary_rank"),
        ]
    )
    n = len(df)

    df = df.with_columns(
        pl.when(
            (pl.col("frequency_rank") > n * 0.75)
            & (pl.col("monetary_rank") > n * 0.75)
            & (pl.col("recency_rank") < n * 0.5)
        )
        .then(pl.lit("champions"))
        .when(
            (pl.col("frequency_rank") > n * 0.5) | (pl.col("monetary_rank") > n * 0.5)
        )
        .then(pl.lit("loyal"))
        .when(pl.col("recency_rank") > n * 0.75)
        .then(pl.lit("lost"))
        .otherwise(pl.lit("at_risk"))
        .alias("segment")
    )
    return df
