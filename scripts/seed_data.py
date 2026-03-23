"""CLI: python -m scripts.seed_data"""
from __future__ import annotations

import sys
sys.path.insert(0, "src")

from retail.data.seed import seed_database


def main() -> None:
    counts = seed_database()
    print(
        f"Seeded {counts['customers']} customers, "
        f"{counts['transactions']} transactions, "
        f"{counts['products']} products"
    )
    print(
        f"RFM segments: champions: {counts['champions']}, "
        f"loyal: {counts['loyal']}, "
        f"at_risk: {counts['at_risk']}, "
        f"lost: {counts['lost']}"
    )
    print("Database: retail.db")


if __name__ == "__main__":
    main()
