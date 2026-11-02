# Sprint 2 frontend starter files

Deadline: Friday, October 30, 2026. These are starter components for teammates
to extend. They are not wired into the existing app.py by this change.

| Owner | Assigned file | Next work |
|---|---|---|
| Brigitte | request_input.py | Input UI, examples, loading state, Gemini integration |
| Chenfei | request_feedback.py | Missing/invalid input, supported categories, API errors |
| Set | product_display.py | Catalog-backed product cards and available stock |
| Yashmit | cart_display.py | Quantity editing/removal, totals, budget and stock checks |
| Andrew | checkout.py | Approved cart to PayPal Sandbox order and approval link |
| Integration Lead | app.py (later) | Connect components and persist state |

Work primarily in your assigned file on a feature branch and open a pull
request. Coordinate function signature changes with the Integration Lead.

## Existing backend contracts

- parser.parse_request(message) returns a dictionary with budget, people,
  categories, and priority. It currently uses a mock parser, not Gemini.
- optimizer.recommend_cart(request, catalog) returns a list of
  `{"id": "chips", "quantity": 1}` dictionaries.
- main.load_catalog() loads data/products.json as a dictionary keyed by ID.
  Prices are strings. Stock is not present; show "Not provided" until the
  team adds it. catalog.py and validator.py do not exist yet.
- optimizer.calculate_total(cart, catalog) returns a Decimal using catalog
  prices. Never supply frontend or LLM prices to checkout.
- paypal_api.create_order(cart, catalog) currently returns a simulated order
  with no approval URL. Real Sandbox checkout is still backend work.

The components accept data and return results. The future app.py integration
should store the request, recommendation, edited cart, and cart_version in
st.session_state; increment cart_version for each new recommendation; and
clear stale carts/orders/approval after new input or failed validation.
The current app.py continues to run its existing UI until integration.

## Suggested integration sequence

1. Call render_request_input() to get `(request, error)`. `(None, None)` means
   there was no submission: keep the existing session state on that rerun.
2. On submission, call render_request_feedback(request, error). Only call
   recommend_cart() after valid feedback. Persist the resulting recommendation.
3. Load the trusted catalog with main.load_catalog() and pass recommendations
   to render_product_display(cart, catalog).
4. Call render_cart_display(cart, catalog, request["budget"], cart_version).
   Persist its return value as the edited cart. Zero quantities remove items.
5. Pass that edited cart, catalog, and budget to render_checkout(). Cart changes
   require renewed approval. The server must repeat all validation before
   creating a real order; these UI checks do not replace backend validation.

All render functions must be called within a Streamlit app. Install the existing
requirements and run `streamlit run app.py` for the current application; import
these components into a local scratch Streamlit entry point to preview your
assigned component before integration.

## Manual demo scenarios

- Brigitte: try all three examples in EXAMPLE_REQUESTS and an empty submission.
- Chenfei: pass budget=None, budget=-10, and a valid budget with categories;
  pass an error string to exercise API failure feedback. The mock parser fills
  missing budgets with $50, so missing-budget detection needs parser coordination.
- Set: use `[{"id": "chips", "quantity": 1}]` with main.load_catalog(); confirm
  the name/price match the JSON and unknown IDs show feedback.
- Yashmit: edit a quantity, remove it with zero, and exceed a $10 budget. Add a
  stock field to a local test catalog to exercise the stock warning.
- Andrew: confirm an empty or over-budget cart is blocked, an edited cart needs
  new approval, and approved checkout returns a DEMO order with no payment link.

Next milestone: integrated Gemini → Streamlit → PayPal Sandbox flow including
capture by Wednesday, November 4, 2026.
