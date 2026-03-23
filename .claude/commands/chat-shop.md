# chat-shop

Starts an interactive terminal shopping session using the Claude-powered assistant.

## What it does
- Loads the customer's profile and recommendations
- Starts a multi-turn conversation with the Claude shopping assistant
- Demonstrates tool_use: search_catalogue, get_recommendations, add_to_basket, place_order
- Shows streaming responses with Rich-styled terminal output

## Usage
```
/chat-shop <customer_id>
```

Example:
```
/chat-shop CUS_00000001
```

## Implementation
Set your ANTHROPIC_API_KEY in .env first, then:

```bash
python -c "
import asyncio
from retail.assistant.assistant import ShoppingAssistant
from retail.domain.customer import ShopperProfile

# Load profile, start session, run REPL
asyncio.run(main('CUS_00000001'))
"
```

## Example Conversation
```
You: Buy my usual groceries, I need them tomorrow morning
Assistant: I'll check your recommendations and add your top items...
[uses get_recommendations tool]
[uses add_to_basket tool x3]
I've added 3 items to your basket:
- Organic Milk x2 (£2.40)
- Sourdough Bread x1 (£2.80)
- Free Range Eggs x1 (£3.20)
Total: £8.40. Shall I place this for tomorrow 9am-1pm delivery?

You: Yes please
Assistant: [uses place_order tool]
Order confirmed! Order #ORD-1234 for tomorrow 9am-1pm. 🎉
```

## Notes
- Requires ANTHROPIC_API_KEY in .env
- Requires seeded data and pipeline to have run
