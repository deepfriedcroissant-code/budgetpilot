# BudgetPilot integration lead handoff

This is a **separate review branch**, based on `integration/backend-oct27`.
It intentionally does **not** edit `app.py`, `optimizer.py`, `parser.py`,
`paypal_api.py`, `ui/*`, or the existing teammate feature branches.

## What this branch adds

- `integration_preview.py`: independent Streamlit smoke demo for the backend
  request → catalog → optimizer → editable cart → PayPal Sandbox order-creation
  handoff. Offline mode works with sample structured input, with no API calls.
- `docs/INTEGRATION_ACCEPTANCE.md`: the final PR and milestone checklist.

## How to use the preview

Start from this branch (or merge into the final integration branch):

```bash
python -m pip install -r requirements.txt
streamlit run integration_preview.py
```

The default **sample structured request** mode does not call Gemini or PayPal
until the user explicitly chooses to create a PayPal order. It verifies the
request-to-cart contract using Set's catalog and the backend optimizer.

To test *live* Gemini, use the second mode and set `GEMINI_API_KEY` in a
**local, ignored** `.env` file. To create an actual PayPal Sandbox order,
configure the REST Sandbox client ID and secret locally. Never commit keys.

Important: the preview does NOT perform PayPal return URL handling, persistent
order/session correlation, capture verification, production payments, or final
full frontend integration. Do not claim a transaction is paid merely because
an approval link was created.

## Working with the team

- Brigitte owns `parser.py` and `ui/request_input.py`.
- Chenfei owns `validator.py` and `ui/request_feedback.py`.
- Set owns `catalog.py`, catalog data, and `ui/product_display.py`.
- Yashmit owns `optimizer.py` and `ui/cart_display.py`.
- Andrew owns `paypal_api.py` and `ui/checkout.py`.
- Integration lead owns the final `app.py`, merges, and acceptance testing.

Yashmit's improved optimizer on `yashmit/cart-display` should replace the
baseline version in the **final combined branch** after conflict resolution.
This preview calls the stable `recommend_cart(request, catalog)` contract, so
it should work with either implementation.

Do NOT merge the older `gemini_parser` fallback that invents a budget when
the user omits it; that defeats missing-budget validation.

## Credential safety

Earlier project history included API credentials in `.env.example`.
The integrated branch's file now uses placeholders, but Git history is still
exposed to anyone with repository access. Rotate affected Gemini/PayPal
credentials before relying on them, and avoid echoing secrets into CI logs.

## Branch/PR ordering

1. Review `integration/backend-oct27` (draft PR #3).
2. Review Yashmit's PR #2 and adapt its improved optimizer.
3. Review `codex/sprint-2-frontend-starters` (PR #1); avoid applying the
   shared starter files twice when incorporating Yashmit's branch.
4. Integrate the final `app.py` using the team's component functions.
5. Verify live Gemini and PayPal Sandbox payment capture before demo signoff.

Treat this new preview PR as **optional scaffolding** for the integration lead.
It is safe to leave unmerged if the team prefers the final `app.py` only.
