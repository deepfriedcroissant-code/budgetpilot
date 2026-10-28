# BudgetPilot — PayPal AI Hackathon

AI-assisted budget shopping. This branch contains a **temporary integrated
backend**, not a finished frontend or verified live PayPal payment.

## Backend workflow

User message → Gemini `parse_request` → `validate_request` →
46-product `load_catalog` → `recommend_cart` →
`calculate_total` → user cart approval → PayPal Sandbox order.

## Getting started

```bash
python -m pip install -r requirements.txt
pytest -q
python main.py
streamlit run app.py
```

`python main.py` uses a hardcoded parsed request for an offline smoke demo.
The current `app.py` is the original mock Streamlit frontend; UI work lives
in PR #1 and PR #2 and is intentionally not included in this backend PR.

To try live Gemini, copy `.env.example` to `.env` (never commit `.env`),
set your Gemini key, and run:

```python
from main import build_cart
request, cart, catalog = build_cart("Snacks and drinks for 20 people under $100")
print(request, cart)
```

For a PayPal Sandbox order, use `paypal_api.create_order(cart, catalog,
budget=request["budget"])` with a trusted catalog; this creates an approval
URL but does not capture or verify payment.

## Important limitations

- MVP optimizer uses a one-of-each-item selection. Group size, multiple
  quantities, and shopping priorities need Yashmit's next update.
- The PayPal Sandbox approval/return/capture verification workflow is not
  finished; no production payments.
- Live Gemini/PayPal requests were not run by offline unit tests.
- **Rotate previously committed credentials.** This branch replaces
  `.env.example` with placeholders; older commits still contain its history.

See [INTEGRATION_NOTES.md](INTEGRATION_NOTES.md) for shared function contracts
and handoff responsibilities.
