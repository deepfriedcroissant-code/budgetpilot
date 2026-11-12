# BudgetPilot — PayPal AI Hackathon

**BudgetPilot** is a prototype AI budget-shopping assistant: describe a shopping need in natural language, receive product suggestions, customize an editable cart, stay within budget, and approve checkout through the **PayPal Sandbox Orders API**.

### Vision and demo scope

BudgetPilot is envisioned as a shopping-assistance feature inside PayPal: beyond discovering merchants, users could get help deciding **what to buy, how much to buy, and how to stay within a budget**. Connecting real merchants and live inventories was outside this hackathon prototype's scope, so the demo uses a **local, static 46-product catalog**. Prices and stock checks come from that catalog; they are not sourced from Gemini or live stores.

## Features

- **Natural-language intent parsing:** Google Gemini extracts shopping budget, group size, categories and priority from user requests.
- **Catalog-grounded recommendations:** an optimizer selects quantities based on the parsed request, trusted prices, budget and available stock. Product cards include concise, grounded recommendation explanations.
- **Editable cart and live dashboard:** quantity changes immediately update the validated total, remaining budget, item counts and shopping progress.
- **Reviewable budget fixes:** if a cart exceeds its budget or stock limits, BudgetPilot suggests quantity reductions. Changes require explicit user approval.
- **PayPal Sandbox checkout:** server-side cart validation, Orders v2 creation, Sandbox buyer approval, persisted order/return-state validation, capture and verification.
- **Accurate payment statuses:** a capture marked `PENDING` (including `PENDING_REVIEW`) displays **Payment pending**, not **Payment successful**. Users can refresh the existing order status through a read-only API call, without another capture request. A receipt is shown only when the capture is verified `COMPLETED`. Duplicate captures are guarded against.

**Important:** PayPal **Sandbox** is test infrastructure. This prototype never initiates production payments. It does not connect to real merchant inventory, fulfill orders, handle shipping/taxes, or reserve stock. An approved order and an order-level `COMPLETED` response do **not** prove the underlying capture is `COMPLETED`.

## Built with

Python · Streamlit · Google Gemini (`google-genai`) · PayPal Orders v2 Sandbox API · Requests · SQLite · Python dotenv · Pytest · JSON catalog

## Run locally

Use Python 3.11+ and run:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Create a local `.env` from `.env.example`. To enable live intent parsing, set `GEMINI_API_KEY` and `GEMINI_MODEL=gemini-3.1-flash-lite` (or another model available to your account). The built-in example request can be used without a Gemini key.

To enable checkout with the team's **Sandbox Business REST app** credentials:

```dotenv
PAYPAL_CLIENT_ID=your_sandbox_business_app_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_business_app_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
APP_URL=http://localhost:8501
BUDGETPILOT_ENABLE_PAYPAL_SANDBOX=1
```

Approve using a **separate PayPal Sandbox Personal buyer** account. Do not use live PayPal credentials or commit `.env`.

## Demo walkthrough

1. Enter a shopping request such as *snacks and drinks for 20 people, budget $100* (or use the example button).
2. Review recommended products and expand **Why this pick?**.
3. Increase cart quantities to exceed the budget; inspect **Make your cart fit** and choose **Apply suggested changes**.
4. Review the cart, approve checkout, and continue to PayPal Sandbox with a test buyer.
5. On return, inspect the **verified completed** or **pending-review** state. The **Check payment status** action is read-only and never resubmits the capture.
6. If desired, show the corresponding merchant-side Sandbox transaction activity, without exposing account credentials.

## Tests and release

The latest final-demo branch was verified by GitHub Actions with **81 passing automated tests and one non-blocking warning** on commit `2caa3a80fb4cb68c3b5675691e5c817568dbdc5a`. The suite covers cart and catalog behavior, checkout validation, pending-review handling, one-time capture, read-only reconciliation and recommendation UI contracts.

**Live Sandbox observation:** A Sandbox buyer-approved transaction reached PayPal and appeared in the merchant's email, but its capture was `PENDING` with reason `PENDING_REVIEW` due to a temporary hold. It was not yet a verified completed capture. A final end-to-end **COMPLETED** capture has not been independently confirmed.

Local browser and external API behavior require additional manual testing; CI uses mocks for PayPal and does not certify a production-ready deployment. See [docs/COMBINED_FRONTEND.md](docs/COMBINED_FRONTEND.md) for additional team-integration notes.
