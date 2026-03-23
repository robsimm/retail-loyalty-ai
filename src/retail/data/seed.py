from __future__ import annotations

import random
import sqlite3
import uuid
from datetime import datetime, timedelta

CATEGORIES = [
    "grocery", "dairy", "bakery", "produce", "meat",
    "frozen", "beverages", "snacks", "household", "personal_care",
]

AGE_BRACKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
CHANNELS = ["online", "instore", "both"]
SEGMENTS = ["champions", "loyal", "at_risk", "lost"]

SEGMENT_CONFIG = {
    "champions":  {"freq_range": (40, 60),  "days_ago_range": (1, 14),   "spend_range": (20, 80)},
    "loyal":      {"freq_range": (20, 40),  "days_ago_range": (14, 45),  "spend_range": (15, 60)},
    "at_risk":    {"freq_range": (5, 20),   "days_ago_range": (45, 120), "spend_range": (10, 40)},
    "lost":       {"freq_range": (1, 5),    "days_ago_range": (120, 365),"spend_range": (5, 20)},
}


def seed_database(db_path: str = "retail.db", n_customers: int = 1000) -> dict[str, int]:
    """Seed SQLite with synthetic retail data. Returns counts."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            age_bracket TEXT,
            channel_preference TEXT,
            signup_date TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            price_gbp REAL,
            is_high_consideration INTEGER DEFAULT 0,
            available_online INTEGER DEFAULT 1,
            available_instore INTEGER DEFAULT 1
        );

        CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            customer_id TEXT,
            amount_gbp REAL,
            category TEXT,
            timestamp TEXT,
            channel TEXT,
            is_return INTEGER DEFAULT 0
        );
    """)

    # Seed products (200)
    products = []
    for i in range(1, 201):
        cat = CATEGORIES[(i - 1) % len(CATEGORIES)]
        price = round(random.uniform(0.50, 25.00), 2)
        products.append((
            f"PRD_{i:05d}",
            f"{cat.title()} Item {i}",
            cat,
            price,
            1 if price > 15 else 0,
            1, 1,
        ))
    cur.executemany(
        "INSERT INTO products VALUES (?,?,?,?,?,?,?)", products
    )

    # Seed customers + transactions
    all_transactions = []
    segment_counts: dict[str, int] = {s: 0 for s in SEGMENTS}

    segment_labels = (
        ["champions"] * 120 + ["loyal"] * 380 + ["at_risk"] * 300 + ["lost"] * 200
    )
    random.shuffle(segment_labels)

    for i in range(n_customers):
        cid = f"CUS_{i+1:08d}"
        age = random.choice(AGE_BRACKETS)
        channel = random.choice(CHANNELS)
        signup = (datetime.now() - timedelta(days=random.randint(180, 1800))).date().isoformat()
        cur.execute(
            "INSERT INTO customers VALUES (?,?,?,?,?)", (cid, age, channel, signup, 1)
        )

        segment = segment_labels[i]
        cfg = SEGMENT_CONFIG[segment]
        segment_counts[segment] += 1

        n_tx = random.randint(*cfg["freq_range"])
        for _ in range(n_tx):
            days_ago = random.randint(*cfg["days_ago_range"])
            ts = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
            cat = random.choice(CATEGORIES)
            amount = round(random.uniform(*cfg["spend_range"]), 2)
            if channel in ("online", "instore"):
                ch = channel
            else:
                ch = random.choice(["online", "instore"])
            all_transactions.append((
                str(uuid.uuid4()), cid, amount, cat, ts, ch, 0
            ))

    cur.executemany(
        "INSERT INTO transactions VALUES (?,?,?,?,?,?,?)", all_transactions
    )

    conn.commit()
    conn.close()

    return {
        "customers": n_customers,
        "transactions": len(all_transactions),
        "products": len(products),
        **segment_counts,
    }
