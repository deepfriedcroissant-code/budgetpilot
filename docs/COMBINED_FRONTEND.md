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
GEMINI_MODEL=gemini-3.1-flash-lite
```

If you already have a local `.env`, edit its `GEMINI_MODEL` line too; Git does
not update private, untracked `.env` files. Verify with
`python scripts/check_gemini.py` before launching Streamlit.

The Gemini 3.1 Flash-Lite parser requests JSON for four-field intent extraction.
The model is configurable via `GEMINI_MODEL`. The VS Code / Streamlit terminal logs only
Gemini model ID and API elapsed seconds for performance testing. It does not
log your request or credentials. Do not put real keys in `.env.example`.

PayPal Sandbox is **disabled by default**. To test the complete flow, place
Sandbox credentials in the uncommitted local `.env` alongside `app.py`:

```dotenv
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
APP_URL=http://localhost:8501
BUDGETPILOT_ENABLE_PAYPAL_SANDBOX=1
```

Create a cart, explicitly approve it, create the order, then click the Sandbox
approval link and sign in as a **Sandbox buyer**. PayPal redirects back to
BudgetPilot with a one-time verification state; BudgetPilot retrieves a matching
locally stored order, captures once, and verifies COMPLETED status, amount, and
currency before displaying success. It stores local order state in an ignored
SQLite file under `.budgetpilot/` so it works across Streamlit browser sessions.

**Limitations:** Sandbox only; manual browser approval is required. The live
Google Gemini and PayPal APIs have not been verified by CI. Local SQLite is
suitable for a single-machine demo, not a distributed hosting deployment.
If a capture produces an unknown result, the app blocks automatic retries:
inspect the order in the Sandbox dashboard first to avoid double capture.
Restarting the server from a different directory is safe; deleting the
`.budgetpilot/` directory loses the local order verification records.

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
- Complete a real Sandbox buyer approval/capture smoke test and verify the exact total in the Sandbox dashboard.
- Rotate API secrets exposed in earlier git history.
