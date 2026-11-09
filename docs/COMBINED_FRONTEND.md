# Combined Streamlit Frontend — Integration Candidate

This branch is a **standalone integration candidate**, based on the earlier
backend integration, and is not merged into `main`. It combines the latest
committed versions of Brigitte's request form, Chenfei's feedback (adapted into
`ui/request_feedback.py`), Set's product cards, Yashmit's editable cart and
improved optimizer, and Andrew's checkout section.

## Run the combined website

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Click **Try sample** to use a fixed request without Gemini/API credentials.
For natural-language input, create a local uncommitted `.env` next to `app.py`:

```dotenv
GEMINI_API_KEY=your_new_google_ai_studio_api_key
GEMINI_MODEL=gemini-3.8-flash
```

The Gemini 3.8 Flash parser uses `low` thinking to reduce latency for the four-field
intent extraction. The model is configurable via `GEMINI_MODEL`; other model IDs
are not forced to use this setting. The VS Code / Streamlit terminal logs only
Gemini model ID and API elapsed seconds for performance testing. It does not
log your request or credentials. Do not put real keys in `.env.example`.

PayPal Sandbox is **disabled by default**. When Andrew and the integration lead
are ready for Sandbox tests, configure the local credentials and explicitly
set `BUDGETPILOT_ENABLE_PAYPAL_SANDBOX=1` in the environment. Merely creating
an order does not capture a payment. The return-and-capture flow still requires
implementation and verification before a successful-payment claim.

## Source attribution / ownership

- Brigitte: `ui/request_input.py`
- Chenfei: `ui/request_feedback.py` adapted from `request_feedback_with_scenarios.py`
- Set: `ui/product_display.py` and its tests
- Yashmit: `ui/cart_display.py`, `optimizer.py`, workflow tests
- Andrew: `ui/checkout.py`
- Integration lead: `app.py`, shared session state / feature gating

**Review this branch before merging.** This branch preserves all teammates'
existing branches and PRs. Refresh code from teammates if they push new commits.

## Known follow-ups

- Run live Gemini samples, including ambiguous/missing-budget cases.
- Test that quantity edits invalidate prior checkout approval/order state.
- Finish PayPal order approval return, capture, and amount verification.
- Rotate API secrets exposed in earlier git history.
