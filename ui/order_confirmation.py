"""Verified PayPal Sandbox completion experience."""
from decimal import Decimal
import streamlit as st


def render_verified_confirmation(result):
    """Show a receipt only for a completed, verified PayPal capture."""
    if not isinstance(result, dict) or result.get("status") != "COMPLETED":
        raise ValueError("A verified completed capture is required.")
    if not result.get("order_id") or not result.get("capture_id"):
        raise ValueError("Missing verified PayPal reference.")
    amount = Decimal(str(result["total"]))
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Invalid verified payment amount.")
    st.markdown(
        '<div class="bp-success bp-pop" role="status">'
        '<div class="bp-success-icon">✓</div>'
        '<h2>Payment successful!</h2>'
        '<p>Your PayPal Sandbox payment has been securely verified.</p>'
        '</div>', unsafe_allow_html=True,
    )
    st.success("Verified capture · COMPLETED · Sandbox transaction")
    a, b = st.columns(2)
    a.metric("Paid", f"USD ${amount:,.2f}")
    b.metric("Payment provider", "PayPal Sandbox")
    st.caption("PayPal order reference")
    st.code(str(result["order_id"]), language=None)
    st.caption("Capture reference")
    st.code(str(result["capture_id"]), language=None)
    st.info("This was a Sandbox demonstration payment. No real money was transferred.")
