"""BudgetPilot combined Streamlit frontend — pre-PayPal integration candidate.

This app combines team UI components against the shared backend contracts.
PayPal sandbox order creation is DISABLED by default until intentionally enabled.
Run: streamlit run app.py
"""
import os
from decimal import Decimal

import streamlit as st

from catalog import CATEGORIES, load_catalog
from optimizer import recommend_cart, calculate_total
from ui.request_input import render_request_input
from ui.request_feedback import render_request_feedback
from ui.product_display import render_product_display
from ui.cart_display import render_cart_display

st.set_page_config(page_title="BudgetPilot | AI Shopping Assistant", page_icon="🛒", layout="wide")

SAMPLE_REQUEST = {
    "budget": 100.0,
    "people": 20,
    "categories": ["snacks", "drinks"],
    "priority": "variety",
}


def _clear_checkout_state() -> None:
    """Invalidate stale approvals and orders whenever request/cart changes."""
    for key in list(st.session_state.keys()):
        if key.startswith("checkout_approved_") or key in (
            "checkout_order_result", "checkout_error", "checkout_cart_fp",
            "budgetpilot_cart_valid", "budgetpilot_cart_changed",
        ):
            st.session_state.pop(key, None)


def _apply_request(request: dict) -> None:
    """Validate once, load trusted catalog, and produce new recommendation."""
    from validator import validate_request
    validate_request(request)
    catalog = load_catalog()
    recommended = recommend_cart(request, catalog)
    if calculate_total(recommended, catalog) > Decimal(str(request["budget"])):
        raise ValueError("Cart exceeds available budget.")

    st.session_state.bp_request = request
    st.session_state.bp_catalog = catalog
    st.session_state.bp_recommendations = recommended
    st.session_state.bp_cart_version = st.session_state.get("bp_cart_version", 0) + 1
    st.session_state.bp_current_cart = list(recommended)
    st.session_state.bp_error = None
    _clear_checkout_state()


def _clear_request(error: str | None) -> None:
    st.session_state.bp_request = None
    st.session_state.bp_catalog = None
    st.session_state.bp_recommendations = []
    st.session_state.bp_current_cart = []
    st.session_state.bp_error = error
    st.session_state.bp_cart_version = st.session_state.get("bp_cart_version", 0) + 1
    _clear_checkout_state()


for key, value in (
    ("bp_request", None),
    ("bp_catalog", None),
    ("bp_recommendations", []),
    ("bp_current_cart", []),
    ("bp_error", None),
    ("bp_cart_version", 0),
):
    if key not in st.session_state:
        st.session_state[key] = value

st.title("BudgetPilot")
st.caption("AI-assisted shopping that respects your budget. · Integration preview")
st.markdown(
    "Describe your shopping needs, review real catalog recommendations, "
    "and adjust your cart before checkout."
)

with st.sidebar:
    st.header("Integration status")
    st.success("Catalog + validation + optimizer connected")
    st.info("Live Gemini requires GEMINI_API_KEY in your local environment.")
    st.warning("PayPal Sandbox disabled until checkout verification.")
    st.caption("This preview uses the team's Streamlit components.")

st.divider()
st.subheader("1 · Your shopping request")
st.caption(
    "Use Brigitte's form for Gemini parsing, or choose the offline sample "
    "to test the end-to-end cart UI without credentials."
)
sample_clicked = st.button("Try sample: snacks + drinks for 20 people, $100", type="secondary")
parsed, parse_error = render_request_input()

if sample_clicked:
    _clear_request(None)
    try:
        _apply_request(dict(SAMPLE_REQUEST))
    except Exception as exc:
        _clear_request(str(exc))
elif parse_error is not None or parsed is not None:
    _clear_request(parse_error)
    if parsed is not None:
        try:
            _apply_request(parsed)
        except (ValueError, TypeError, KeyError) as exc:
            _clear_request(str(exc))
        except Exception:
            _clear_request("Something went wrong generating recommendations.")

request = st.session_state.bp_request
if st.session_state.bp_error is not None:
    render_request_feedback(None, st.session_state.bp_error)
elif request is not None:
    render_request_feedback(request, supported_categories=CATEGORIES)

if request is not None:
    catalog = st.session_state.bp_catalog
    recommended = st.session_state.bp_recommendations
    st.divider()
    st.subheader("2 · Your recommended products")
    st.caption(
        f"Budget: ${request['budget']:,.2f}  ·  "
        f"People: {request.get('people') or 'Not specified'}  ·  "
        f"Priority: {request.get('priority') or 'variety'}"
    )
    render_product_display(recommended, catalog, layout="cards", columns=3)

    st.divider()
    st.subheader("3 · Adjust quantities & budget")
    edited = render_cart_display(
        recommended, catalog, request["budget"], st.session_state.bp_cart_version
    )
    if edited != st.session_state.bp_current_cart:
        _clear_checkout_state()
        st.session_state.bp_current_cart = edited

    valid = bool(st.session_state.get("budgetpilot_cart_valid", False))
    st.divider()
    st.subheader("4 · Checkout")
    if not valid:
        st.warning("Adjust the cart to stay within budget and stock before checkout.")
    if os.getenv("BUDGETPILOT_ENABLE_PAYPAL_SANDBOX") == "1":
        # Keep Andrew's checkout callable behind an explicit local opt-in.
        from ui.checkout import render_checkout
        render_checkout(
            edited, catalog, budget=request["budget"],
            cart_valid=valid, cart_version=st.session_state.bp_cart_version,
        )
        st.caption(
            "Sandbox order creation is not completed payment. "
            "Return, capture and verification remain to be implemented."
        )
    else:
        if valid:
            st.success("Your cart is ready for checkout.")
        st.button("PayPal Sandbox checkout — available after integration", disabled=True)
        st.caption(
            "Sandbox calls are intentionally off in this combined frontend "
            "until payment-return and capture verification are tested."
        )
else:
    st.info("Enter a request or try the sample above to see product recommendations.")
