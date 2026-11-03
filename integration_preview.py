"""Independent Streamlit integration smoke-demo for BudgetPilot.

This file intentionally does not edit app.py or teammates' ui/* modules.
Run: streamlit run integration_preview.py

It can test a complete *request-to-cart* flow using deterministic sample intent,
or live Gemini. Sandbox checkout creates an order and approval link only;
secure return/capture processing is not implemented in this preview.
"""
import hashlib
import json
from decimal import Decimal

import streamlit as st

from main import build_cart, build_cart_from_request
from optimizer import calculate_total
from paypal_api import create_order


SAMPLE_REQUEST = {
    "budget": 100.0,
    "people": 20,
    "categories": ["snacks", "drinks"],
    "priority": "variety",
}


def cart_signature(cart: list[dict]) -> str:
    """Stable signature for approval invalidation on any cart edit."""
    normalized = sorted((item["id"], item["quantity"]) for item in cart)
    payload = json.dumps(normalized, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def reset_preview() -> None:
    """Clear approvals/orders when generating a fresh recommendation."""
    st.session_state.preview_version = st.session_state.get("preview_version", 0) + 1
    st.session_state.preview_order = None
    st.session_state.preview_order_signature = None


st.set_page_config(page_title="BudgetPilot integration preview", page_icon="🛒")
st.title("BudgetPilot — Integration Preview")
st.caption(
    "Temporary integration-lead smoke demo. It does not replace app.py "
    "or any teammate's assigned Streamlit components."
)

with st.form("preview_request"):
    mode = st.radio(
        "Source of shopping requirements",
        ["Sample structured request (offline)", "Live Gemini (requires .env)"],
    )
    prompt = st.text_area(
        "Shopping request",
        "Snacks and drinks for 20 people under $100, prioritize variety",
    )
    if mode.startswith("Sample"):
        st.caption("Offline mode uses the fixed example shown below; typed text is not parsed.")
    submitted = st.form_submit_button("Generate recommendation")

if submitted:
    # Invalidate prior user approval and existing order on EVERY new request,
    # including requests that fail validation or Gemini processing.
    reset_preview()
    st.session_state.pop("preview_result", None)
    try:
        with st.spinner("Preparing recommended cart…"):
            result = (
                build_cart_from_request(dict(SAMPLE_REQUEST))
                if mode.startswith("Sample")
                else build_cart(prompt)
            )
        st.session_state.preview_result = result
    except Exception as exc:
        st.error(f"Request could not be processed: {type(exc).__name__}: {exc}")

result = st.session_state.get("preview_result")
if result is not None:
    request, original_cart, catalog = result
    st.subheader("Validated shopping requirements")
    st.json(request)

    version = st.session_state.get("preview_version", 0)
    revised_cart = []
    st.subheader("Review and edit the recommended cart")
    for item in original_cart:
        product_id = item["id"]
        product = catalog[product_id]
        stock = int(product["stock"])
        left, right = st.columns([4, 2])
        with left:
            st.write(f"**{product['name']}**")
            st.caption(
                f"{product['category']} · ${Decimal(str(product['price'])):.2f} "
                f"per unit · {stock} available"
            )
        with right:
            quantity = st.number_input(
                f"Quantity of {product['name']}",
                min_value=0,
                max_value=stock,
                value=min(stock, int(item["quantity"])),
                step=1,
                key=f"preview_qty_{version}_{product_id}",
            )
        if quantity:
            revised_cart.append({"id": product_id, "quantity": int(quantity)})

    valid = bool(revised_cart)
    total = Decimal("0.00")
    if valid:
        try:
            total = calculate_total(revised_cart, catalog)
        except (ValueError, KeyError, TypeError) as exc:
            valid = False
            st.error(f"Invalid cart: {exc}")

    remaining = Decimal(str(request["budget"])) - total
    col1, col2 = st.columns(2)
    col1.metric("Cart total", f"${total:.2f}")
    col2.metric("Remaining budget", f"${remaining:.2f}")
    if not revised_cart:
        st.warning("Your cart is empty.")
    if remaining < 0:
        st.warning("Your edited cart exceeds your budget.")
        valid = False

    current_signature = cart_signature(revised_cart)
    approved = st.checkbox(
        "I approve these items and the displayed total",
        key=f"preview_approval_{version}_{current_signature}",
        disabled=not valid,
    )
    st.divider()
    st.subheader("PayPal Sandbox handoff")
    st.caption(
        "This preview can CREATE a PayPal Sandbox order only. "
        "An approval URL is not evidence of captured payment. "
        "Return handling and verified capture belong to the final checkout."
    )
    if st.button("Create sandbox order", disabled=not (valid and approved)):
        # The backend independently recalculates total/stock/budget.
        try:
            with st.spinner("Creating PayPal Sandbox order…"):
                order = create_order(
                    revised_cart, catalog, budget=request["budget"]
                )
            st.session_state.preview_order = order
            st.session_state.preview_order_signature = current_signature
        except Exception as exc:
            st.session_state.preview_order = None
            st.error(f"Order creation failed: {type(exc).__name__}: {exc}")

    # Orders from old cart versions/edits cannot be reused.
    order = st.session_state.get("preview_order")
    if order and (
        st.session_state.get("preview_order_signature") == current_signature
    ):
        st.write("Order ID:", order.get("order_id"))
        st.write("Order status:", order.get("status"))
        if order.get("approval_url"):
            st.link_button("Approve in PayPal Sandbox", order["approval_url"])
        else:
            st.warning("No PayPal approval URL was returned.")
