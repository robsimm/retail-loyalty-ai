# seed-data

Seeds the SQLite database with synthetic retail data for development and testing.

## What it does
- Creates 1000 synthetic customers with realistic club-card profiles
- Generates 50,000 transactions across 4 loyalty segments (champions, loyal, at_risk, lost)
- Adds 200 products across 10 categories
- Calculates initial RFM profiles for all customers

## Usage
```
/seed-data
```

## Implementation
Run the seed data script:

```bash
python -m scripts.seed_data
```

Expected output:
```
Seeded 1000 customers, 50000 transactions, 200 products
RFM segments: champions: 120, loyal: 380, at_risk: 300, lost: 200
Database: retail.db
```

If the database already exists, it will be reset. Use this to get a fresh state.
