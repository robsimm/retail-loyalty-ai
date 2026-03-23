# run-pipeline

Runs the Polars ETL pipeline to process raw transactions into RFM profiles.

## What it does
- Loads transactions from the SQLite database
- Deduplicates and validates transaction records
- Calculates RFM (Recency, Frequency, Monetary) scores per customer
- Normalises features for KNN engine consumption
- Segments customers into loyalty tiers
- Updates ShopperProfile records in the database

## Usage
```
/run-pipeline
```

## Implementation
```bash
python -m scripts.run_pipeline
```

Expected output:
```
Processed 50000 transactions → 1000 RFM profiles
Segments: champions: 120, loyal: 380, at_risk: 300, lost: 200
Pipeline completed in 0.8s
```

## Notes
- Requires seeded data (run /seed-data first if the database is empty)
- Idempotent: safe to run multiple times
- Uses Polars lazy evaluation for performance
