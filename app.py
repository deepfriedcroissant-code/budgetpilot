"""BudgetPilot shopping assistant — Streamlit frontend.

This app combines team UI components against the shared backend contracts.
PayPal Sandbox remains opt-in and capture is verified against saved orders.
Run: streamlit run app.py
"""
import os
from decimal import Decimal
from dotenv import load_dotenv

import streamlit as st

load_dotenv()

from catalog import CATEGORIES, load_catalog
from optimizer import recommend_cart, calculate_total
from ui.request_input import render_request_input
from ui.request_feedback import render_request_feedback
from ui.product_display import render_product_display
from ui.cart_display import render_cart_display
from ui.theme import apply_theme

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

apply_theme()
st.markdown(
    '<div class="bp-hero"><h1>BudgetPilot</h1>'
    '<p>Smart shopping, made for your budget. Tell us what you need, '
    'discover a personalized cart, and check out with confidence.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Your shopping journey")
    st.markdown("**1.** Describe what you need")
    st.markdown("**2.** Discover recommendations")
    st.markdown("**3.** Personalize your cart")
    st.markdown("**4.** Check out with PayPal")
    st.divider()
    st.caption("Payments are processed in the PayPal Sandbox demonstration environment.")

st.divider()
st.subheader("1 · Your shopping request")
st.caption("Set a budget, choose what matters, and let BudgetPilot do the planning.")
sample_clicked = st.button("Try an example shopping trip · $100 for 20 people", type="secondary")
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
    st.subheader("2 · Picks for you")
    st.caption(
        f"Budget: ${request['budget']:,.2f}  ·  "
        f"People: {request.get('people') or 'Not specified'}  ·  "
        f"Priority: {request.get('priority') or 'variety'}"
    )
    render_product_display(recommended, catalog, layout="cards", columns=3)

    st.divider()
    st.subheader("3 · Make it yours")
    edited = render_cart_display(
        recommended, catalog, request["budget"], st.session_state.bp_cart_version
    )
    if edited != st.session_state.bp_current_cart:
        _clear_checkout_state()
        st.session_state.bp_current_cart = edited

    valid = bool(st.session_state.get("budgetpilot_cart_valid", False))
    st.divider()
    st.subheader("4 · Secure checkout")
    if not valid:
        st.warning("Adjust the cart to stay within budget and stock before checkout.")
    if os.getenv("BUDGETPILOT_ENABLE_PAYPAL_SANDBOX") == "1":
        # Keep Andrew's checkout callable behind an explicit local opt-in.
        from ui.checkout import render_checkout
        render_checkout(
            edited, catalog, budget=request["budget"],
            cart_valid=valid, cart_version=st.session_state.bp_cart_version,
        )
        st.caption("Demo checkout · PayPal Sandbox · No real charges")
    else:
        if valid:
            st.success("Your cart is ready for checkout.")
        st.button("Checkout unavailable", disabled=True)
        st.caption("Checkout isn't available in this session. Your cart is still saved above.")
else:
    st.info("Describe what you need above to discover your personalized cart.")

# PayPal redirects the buyer back with token=ORDER_ID after approval.
# A fresh Streamlit session is fine: the local SQLite record binds order and nonce.
payment = st.query_params.get("payment")
if payment == "success":
    token = st.query_params.get("token")
    state = st.query_params.get("state")
    st.query_params.clear()
    if os.getenv("BUDGETPILOT_ENABLE_PAYPAL_SANDBOX") != "1":
        st.error("Sandbox checkout is disabled; no capture was attempted.")
    elif not token or not state:
        st.error("PayPal returned without the expected order token and verification state.")
    else:
        from paypal_api import capture_order
        from checkout_flow import finalize_return
        with st.spinner("Verifying and capturing your PayPal Sandbox order..."):
            try:
                result = finalize_return(token, state, capture_order)
            except Exception:
                # A capture may have reached PayPal even if confirmation failed.
                # Do NOT retry automatically; inspect the order in PayPal Sandbox.
                st.error(
                    "Payment could not be verified. Check the order in the PayPal Sandbox "
                    "dashboard before attempting another capture."
                )
            else:
                st.success(
                    f"Sandbox payment verified: order `{result['order_id']}` · "
                    f"capture `{result['capture_id']}` · USD ${result['total']} · COMPLETED"
                )
elif payment == "cancelled":
    st.query_params.clear()
    st.warning("PayPal Sandbox checkout was cancelled. No completed payment is recorded.")
