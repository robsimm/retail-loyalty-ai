# test-knn

Tests the KNN recommendation engine for a specific customer.

## What it does
- Loads the customer's ShopperProfile from the database
- Queries the KNN engine for top 10 personalised recommendations
- Displays similarity scores, preferred categories, and KNN neighbours used

## Usage
```
/test-knn <customer_id>
```

Example:
```
/test-knn CUS_00000001
```

## Implementation
Invoke the recommendation engine directly:

```python
import sys
from retail.recommendations.engine import KNNRecommendationEngine
from retail.recommendations.domain import RecommendationRequest

customer_id = sys.argv[1] if len(sys.argv) > 1 else "CUS_00000001"

# Load profiles from DB, fit engine, predict
request = RecommendationRequest(customer_id=customer_id, top_n=10)
recommendations = engine.predict(request)

for rec in recommendations:
    print(f"{rec.rank}. {rec.product_name} ({rec.category}) — similarity: {rec.similarity_score:.3f}")
    print(f"   Reason: {rec.reason}")
```

## Notes
- Requires pipeline to have been run (profiles must exist)
- High-consideration filter available: /test-knn CUS_00000001 --high-consideration
