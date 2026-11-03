# BudgetPilot final acceptance checklist

## Build and branch readiness
- [ ] Rotate exposed credentials; verify `.env.example` has placeholders.
- [ ] Review and integrate backend PR #3 and Yashmit's updated optimizer.
- [ ] Merge frontend starter and UI contributions without duplicate patches.
- [ ] Install dependencies from a fresh virtual environment.
- [ ] Run `pytest -q` against the **final combined revision**, not just PR #3.

## Request-to-cart MVP
- [ ] Live Gemini request returns the agreed four-field intent dictionary.
- [ ] Missing budget is reported rather than replaced with a fabricated value.
- [ ] Unknown categories are rejected with understandable feedback.
- [ ] Matching in-stock catalog items produce a cart within budget.
- [ ] 0-stock items are never included.
- [ ] Quantity edits update totals from trusted catalog prices.
- [ ] Editing the cart invalidates previous approval and PayPal order state.
- [ ] Regenerating a cart clears stale widget quantities and checkout state.

## PayPal Sandbox MVP
- [ ] Sandbox REST credentials stored only in the local environment.
- [ ] Approved cart's ID, quantity, stock, price and budget are validated server-side.
- [ ] Order-creation returns approval URL and PayPal order ID.
- [ ] User approval returns to the application, with persisted local order binding.
- [ ] Cancellation does not capture payment.
- [ ] Capture is called once per validated order and is idempotent/reconciled.
- [ ] Final capture status, amount and currency verified via PayPal response.
- [ ] UI distinguishes CREATED, APPROVED, COMPLETED, CANCELLED and FAILED.
- [ ] An approval URL is never labeled as completed payment.

## Demonstration and submission
- [ ] Demonstrate 3 requests with differing budgets/categories/priorities.
- [ ] Demonstrate one validation error and one out-of-stock/budget constraint.
- [ ] Demonstrate a complete sandbox payment in a fresh browser session.
- [ ] README documents environment setup and commands accurately.
- [ ] Final demo video, screenshots and submission URLs verified.
- [ ] Freeze scope and reserve time for bugs before the deadline.
