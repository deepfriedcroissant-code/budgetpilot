# BudgetPilot — PayPal AI Hackathon

AI-assisted budget shopping demo. **Current state:** mock request parser and mock checkout; no API keys or real payments required.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or run `python main.py` for a command-line demonstration.

## Team ownership

| Member | File | Responsibility |
|---|---|---|
| 1 | `parser.py` | Gemini API / natural-language parsing |
| 2 | `optimizer.py` | Budget-aware cart selection |
| 3 | `paypal_api.py` | PayPal Sandbox Orders API |
| 4 | `main.py` | Integrate modules, review pull requests |
| 5 | `app.py` | Streamlit interface |
| 6 | `data/products.json`, `tests/` | Product data and tests |

## Shared contracts (agree before changing)

- `parse_request(message: str) -> dict`: `{budget: float, people: int, categories: list[str], priority: str}`
- `recommend_cart(request: dict, catalog: dict) -> list[dict]`: each item `{id: str, quantity: int}`
- `calculate_total(cart, catalog) -> Decimal`: validated total using trusted catalog prices
- `create_order(approved_cart, catalog) -> dict`: `{order_id, status, total, approval_url}`

Never accept LLM-provided prices for payment. Recompute totals from the trusted catalog. Require explicit approval before checkout.

## Collaboration

Use `feature/llm`, `feature/optimizer`, `feature/paypal`, `feature/integration`, `feature/frontend`, `feature/testing` branches. Open pull requests; avoid committing to `main` directly. Never commit secrets.

## Timeline

- Oct 14–20: agree contracts, mock modules, credentials
- Oct 21–27: AI parser, optimizer, frontend; PayPal standalone test
- Oct 28–Nov 3: integration and end-to-end sandbox checkout
- Nov 4–11: testing, demo, documentation and submission
