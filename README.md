# BudgetPilot — PayPal AI Hackathon

BudgetPilot converts natural-language shopping needs into an editable,
budget-aware cart and a PayPal **Sandbox** checkout.

## November 10 release candidate

The combined Streamlit frontend integrates the team components:
- Gemini shopping-intent parsing (Brigitte) and request validation (Chenfei)
- 46-product trusted catalog (Set)
- Quantity-aware, budget/stock-aware optimizer and editable cart (Yashmit)
- PayPal Sandbox order creation and checkout integration (Andrew + integration)

**Payment flow:** cart approval → order creation with trusted catalog prices →
Sandbox buyer approval → return-state check → one-time capture → verify captured
amount, USD currency, and COMPLETED status.

This branch is for review/testing. It is **not merged into main** and has **not
yet passed a live buyer-approved Sandbox checkout**.

## Local quickstart

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/check_gemini.py
python -m streamlit run app.py
```

Create a local `.env` next to `app.py`, using `.env.example` as a guide.
Use `GEMINI_MODEL=gemini-3.1-flash-lite`. The offline sample button requires
no Gemini key. Never commit credentials.

PayPal checkout is off unless `BUDGETPILOT_ENABLE_PAYPAL_SANDBOX=1` is set
locally with valid Sandbox REST credentials and `APP_URL=http://localhost:8501`.
Always log in using a **Sandbox buyer**, not a real PayPal account.

See [docs/COMBINED_FRONTEND.md](docs/COMBINED_FRONTEND.md) for the full demo
procedure, limitations and testing notes.

## Known release gates

- Live Gemini parsing, including missing budget and invalid categories
- Live Sandbox order approval + capture verification and cancellation
- Browser rerender/edit state and cart budget/stock constraints
- All CI tests passing on this release candidate
- Rotate any previously exposed API keys or sandbox credentials

No production charges, live product pricing, shipping, taxes, or inventory
reservation are implemented. Do not claim production checkout support.
