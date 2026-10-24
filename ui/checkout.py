"""Owner: Andrew — explicit cart approval and PayPal Sandbox handoff."""
from decimal import Decimal
import streamlit as st
from optimizer import calculate_total
from paypal_api import create_order


def render_checkout(approved_cart: list[dict], catalog: dict, budget: float) -> None:
    """Starter checkout using the existing backend contract.

    TODO (Andrew): connect the Sandbox implementation, persist order results,
    avoid duplicate orders on retries, and coordinate approval invalidation
    whenever the cart changes. Return/capture handling belongs to integration.
    Backend create_order() must independently validate prices and constraints.
    """
    st.subheader("Checkout")
    st.caption("Current backend simulates checkout; no PayPal payment is made.")
    if not approved_cart:
        st.info("Add products to your cart before checkout.")
        return
    try:
        total = calculate_total(approved_cart, catalog)
        if total <= 0 or total > Decimal(str(budget)):
            raise ValueError("Cart total must be positive and within budget.")
        for item in approved_cart:
            stock = catalog[item["id"]].get("stock")
            if stock is not None and item["quantity"] > stock:
                raise ValueError("A cart quantity exceeds available stock.")
    except (ValueError, KeyError) as exc:
        st.warning(f"Checkout unavailable: {exc}")
        return
    # A changed cart produces a fresh unchecked approval widget.
    signature = repr((approved_cart, catalog, str(budget)))
    approved = st.checkbox("I approve this cart and total", key=f"approve_{signature}")
    if st.button("Proceed to checkout (currently simulated)", disabled=not approved):
        try:
            with st.spinner("Creating your order…"):
                order = create_order(approved_cart, catalog)
            st.write(f"Order ID: {order['order_id']}")
            st.write(f"Status: {order['status']}")
            if order.get("approval_url"):
                st.link_button("Continue to PayPal Sandbox", order["approval_url"])
            else:
                st.info("Simulated order created. No PayPal approval URL is available yet.")
        except Exception:
            st.error("Checkout failed. Please try again later.")
