# Backend integration checkpoint — October 27, 2026

This temporary backend integration branch combines Brigitte's Gemini parser,
Chenfei's validator and tests, Set's 46-product catalog, and Andrew's PayPal
Sandbox API module. The original branches are left untouched.

## Stable contracts for frontend team

- `parser.parse_request(message) -> dict`: dictionary keys: budget, people,
  categories, priority. Budget and categories must be specified by the user.
  People and priority can be None.
- `validator.validate_request(data) -> True` or raises `ValueError`.
- `catalog.load_catalog() -> dict`: keyed by product ID; price is Decimal,
  stock is integer.
- `optimizer.recommend_cart(request, catalog) -> list[dict]`: each entry
  contains only id and positive integer quantity.
- `optimizer.calculate_total(cart, catalog) -> Decimal`: catalog-priced
  total with ID, quantity, and stock checks.
- `main.build_cart(message) -> (request, cart, catalog)`: real Gemini path.
- `main.build_cart_from_request(request) -> (...)`: offline/test path.
- `paypal_api.create_order(cart, catalog, budget=None) -> dict`: keyword-only
  budget is optional in the current signature (currency is the third argument).
  It returns order_id, status, total, approval_url. This creates a Sandbox
  order only, NOT a completed/captured payment.

## Local testing

```bash
pip install -r requirements.txt
pytest -q
python main.py
```

Copy .env.example to .env, configure Gemini and PayPal Sandbox secrets,
and then test live Gemini/PayPal against your sandbox account. Unit tests
mock the API, so passing tests do not prove live credentials/payment work.

## Next actions and limitations

- Yashmit: MVP optimizer currently selects one of each eligible in-stock
  item that fits the remaining budget. Improve multiple-unit recommendations,
  group-size estimates, and variety/budget preferences inside optimizer.py
  WITHOUT changing recommend_cart(request, catalog) -> [{id, quantity}].
- Andrew: verify real Sandbox order creation; implement checkout return
  correlation, idempotent capture, post-capture verification, and persistent
  order storage in the next sprint. Frontend approval must be rechecked after
  any cart edits.
- UI pair: use separate Streamlit component files and mock sample dictionaries
  until integrated app.py is ready. Frontend starter PR #1 and cart PR #2 have
  NOT been merged by this integration branch.
- Integration Lead: test and review this PR before merging. Rotate any API
  credentials previously committed in .env.example or its Git history,
  including forked/cached copies; replacing the file does not erase history.
