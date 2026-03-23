"""CLI: python -m scripts.run_pipeline"""
from __future__ import annotations

import sqlite3
import sys
import time
sys.path.insert(0, "src")

import polars as pl

from retail.pipeline.pipeline import TransactionPipeline


def main() -> None:
    t0 = time.time()
    conn = sqlite3.connect("retail.db")
    df = pl.read_database("SELECT * FROM transactions", conn)
    conn.close()

    pipeline = TransactionPipeline()
    profiles = (
        pipeline
        .load_df(df)
        .validate()
        .transform()
        .aggregate_rfm()
        .to_profiles()
    )

    segments: dict[str, int] = {}
    for p in profiles:
        segments[p.rfm_segment] = segments.get(p.rfm_segment, 0) + 1

    elapsed = time.time() - t0
    print(f"Processed {len(df)} transactions → {len(profiles)} RFM profiles")
    print(f"Segments: " + ", ".join(f"{k}: {v}" for k, v in segments.items()))
    print(f"Pipeline completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
