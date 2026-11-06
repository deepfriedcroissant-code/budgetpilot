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
For natural-language input, put a Gemini key in a local uncommitted `.env`.

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
