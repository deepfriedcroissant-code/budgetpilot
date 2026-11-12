"""BudgetPilot shopping assistant — Streamlit frontend.

This app combines team UI components against the shared backend contracts.
PayPal Sandbox remains opt-in and capture is verified against saved orders.
Run: streamlit run app.py
"""
import os
import logging
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
from ui.shopping_dashboard import build_sidebar_summary, render_shopping_dashboard
from shopping_assistant import suggest_budget_repair

logger = logging.getLogger("budgetpilot.checkout")

st.set_page_config(page_title="BudgetPilot | AI Shopping Assistant", page_icon="🛒", layout="wide")

SAMPLE_REQUEST = {
    "budget": 100.0,
    "people": 20,
    "categories": ["snacks", "drinks"],
    "priority": "variety",
}


def _clear_checkout_state(*, reset_cart_validation: bool = True) -> None:
    """Invalidate stale PayPal approvals/orders without discarding a fresh cart check.

    render_cart_display() calculates budgetpilot_cart_valid on each run.
    Clearing it immediately after a cart edit incorrectly blocks checkout
    until another rerun, even when the updated cart is under budget.
    """
    for key in list(st.session_state.keys()):
        if key.startswith("checkout_approved_") or key in (
            "checkout_order_result", "checkout_error", "checkout_cart_fp",
            "bp_payment_verified",
        ) or (reset_cart_validation and key in (
            "budgetpilot_cart_valid", "budgetpilot_cart_changed",
        )):
            st.session_state.pop(key, None)



def _apply_suggested_cart(proposed_cart: list[dict], original_cart: list[dict], version: int) -> None:
    """Update quantity widgets in a Streamlit callback, before they render.

    Streamlit disallows assigning to a number_input's session key after
    that widget has been instantiated in the same execution.
    """
    quantities = {item["id"]: item["quantity"] for item in proposed_cart}
    for item in original_cart:
        st.session_state[f"cart_{version}_{item['id']}"] = quantities.get(item["id"], 0)
    _clear_checkout_state(reset_cart_validation=False)


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

# PayPal redirects the buyer back with token=ORDER_ID after approval.
# A fresh Streamlit session is fine: the local SQLite record binds order and nonce.
payment = st.query_params.get("payment")
if payment == "success":
    token = st.query_params.get("token")
    state = st.query_params.get("state")
    st.query_params.clear()
    if os.getenv("BUDGETPILOT_ENABLE_PAYPAL_SANDBOX") != "1":
        st.session_state.bp_payment_return_error = "Sandbox checkout is disabled; no capture was attempted."
    elif not token or not state:
        st.session_state.bp_payment_return_error = "PayPal returned without the expected order token and verification state."
    else:
        from paypal_api import capture_order, get_order_status
        from checkout_flow import finalize_return, get_order, check_payment_status
        with st.spinner("Checking your PayPal Sandbox payment..."):
            try:
                existing = get_order(token, state)
                if existing is None:
                    raise ValueError("Unknown or invalid checkout return state.")
                if existing["status"] == "CREATED":
                    result = finalize_return(token, state, capture_order)
                else:
                    # A return can occur more than once. Never capture twice.
                    result = check_payment_status(token, state, get_order_status)
            except Exception as exc:
                logger.exception("Sandbox checkout verification failed for order %s", token)
                st.session_state.bp_payment_return_order = token
                st.session_state.bp_payment_return_error = (
                    "Payment verification is unresolved. No second capture was attempted."
                    if isinstance(exc, (RuntimeError, ValueError))
                    else "Unable to check PayPal Sandbox right now."
                )
            else:
                if result["status"] == "COMPLETED":
                    st.session_state.bp_payment_verified = True
                    st.session_state.bp_verified_receipt = result
                    st.session_state.pop("bp_pending_payment", None)
                else:
                    st.session_state.bp_pending_payment = {
                        "order_id": token,
                        "state": state,
                        "status": result["status"],
                        "capture_id": result.get("capture_id"),
                        "total": result.get("total"),
                        "reason": result.get("reason"),
                    }
elif payment == "cancelled":
    st.query_params.clear()
    st.session_state.bp_payment_return_error = "PayPal Sandbox checkout was cancelled. No completed payment is recorded."


apply_theme()
st.markdown(
    '<div class="bp-hero"><h1>BudgetPilot</h1>'
    '<p>Smart shopping, made for your budget. Tell us what you need, '
    'discover a personalized cart, and check out with confidence.</p></div>',
    unsafe_allow_html=True,
)

# A confirmed payment has its own final screen, including after a redirect
# opens a fresh Streamlit session. Do not render checkout again for this order.
if st.session_state.get("bp_pending_payment"):
    from paypal_api import get_order_status
    from checkout_flow import check_payment_status
    pending = st.session_state.bp_pending_payment
    st.markdown("## Payment status")
    if pending["status"] == "PENDING":
        st.warning("Payment pending — PayPal has received the capture, but it is not yet completed.")
        if pending.get("reason") == "PENDING_REVIEW":
            st.info("PayPal is reviewing this Sandbox payment. You do not need to pay again.")
    elif pending["status"] == "UNSUCCESSFUL":
        st.error("PayPal reports the capture was unsuccessful. Check the Sandbox merchant account.")
    else:
        st.warning("Payment verification is still unresolved. Please check the existing order.")
    st.caption(f"Order reference: {pending['order_id']}")
    if pending.get("capture_id"):
        st.caption(f"Capture reference: {pending['capture_id']}")
    if pending.get("total"):
        st.metric("Submitted Sandbox amount", f"USD ${pending['total']}")
    if st.button("Check payment status", type="primary"):
        try:
            refreshed = check_payment_status(
                pending["order_id"], pending["state"], get_order_status
            )
        except Exception:
            logger.exception("Read-only Sandbox status lookup failed")
            st.error("PayPal status could not be checked. No new payment was initiated.")
        else:
            if refreshed["status"] == "COMPLETED":
                st.session_state.bp_verified_receipt = refreshed
                st.session_state.bp_payment_verified = True
                st.session_state.pop("bp_pending_payment", None)
            else:
                pending.update({
                    "status": refreshed["status"],
                    "capture_id": refreshed.get("capture_id", pending.get("capture_id")),
                    "total": refreshed.get("total", pending.get("total")),
                    "reason": refreshed.get("reason", pending.get("reason")),
                })
            st.rerun()
    st.caption("Status checks are read-only. BudgetPilot will not capture this order again.")
    with st.sidebar:
        st.warning("Payment pending")
        st.caption("Waiting for PayPal Sandbox verification.")
    st.stop()

if st.session_state.get("bp_verified_receipt"):
    from ui.order_confirmation import render_verified_confirmation
    render_verified_confirmation(st.session_state.bp_verified_receipt)
    if st.button("Start a new shopping trip", type="primary"):
        _clear_request(None)
        st.session_state.pop("bp_verified_receipt", None)
        st.session_state.pop("bp_payment_verified", None)
        st.session_state.pop("bp_payment_return_error", None)
        st.rerun()
    # Sidebar totals may be absent on a new session; completion is still clear.
    from ui.shopping_dashboard import render_shopping_dashboard
    with st.sidebar:
        st.success("Checkout complete")
        st.caption("Your payment was verified in PayPal Sandbox.")
    st.stop()

payment_error = st.session_state.pop("bp_payment_return_error", None)
if payment_error:
    st.warning(payment_error)
    st.info(
        "We cannot confirm whether PayPal completed the capture. Check the "
        "order in your PayPal Sandbox dashboard before creating another payment. "
        "The VS Code terminal contains the specific failure reason."
    )
    failed_order = st.session_state.pop("bp_payment_return_order", None)
    if failed_order:
        st.caption(f"PayPal Sandbox order reference: {failed_order}")

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
    render_product_display(recommended, catalog, layout="cards", columns=3, request=request)

    st.divider()
    st.subheader("3 · Make it yours")
    edited = render_cart_display(
        recommended, catalog, request["budget"], st.session_state.bp_cart_version
    )
    if edited != st.session_state.bp_current_cart:
        # Keep the newly calculated cart validity; only invalidate prior
        # payment approval and order details when quantities change.
        _clear_checkout_state(reset_cart_validation=False)
        st.session_state.bp_current_cart = edited
        st.toast("Cart updated", icon="🛒")

    valid = bool(st.session_state.get("budgetpilot_cart_valid", False))
    if edited and not valid:
        st.markdown("#### Make your cart fit")
        st.caption("We'll suggest quantity changes using catalog prices and available stock. Nothing changes until you apply them.")
        try:
            proposed_cart, proposed_changes = suggest_budget_repair(
                edited, catalog, request["budget"]
            )
        except (ValueError, TypeError, KeyError) as exc:
            st.warning(f"Automatic adjustment isn't available: {exc}")
        else:
            if proposed_cart and proposed_changes:
                st.info("Suggested changes: " + "; ".join(proposed_changes))
                st.caption(f"Proposed new total: ${calculate_total(proposed_cart, catalog):,.2f}")
                st.button(
                    "Apply suggested changes", type="secondary",
                    on_click=_apply_suggested_cart,
                    args=(proposed_cart, recommended, st.session_state.bp_cart_version),
                )
            elif not proposed_cart:
                st.warning("No products can fit this budget. Try a different shopping request.")
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

# Render the sidebar *after* the cart controls on each Streamlit rerun.
# This ensures its totals and checkout status reflect the current edited cart.
active_request = st.session_state.bp_request
summary = build_sidebar_summary(
    active_request,
    st.session_state.bp_current_cart,
    st.session_state.bp_catalog,
    st.session_state.get("budgetpilot_cart_valid", False),
    os.getenv("BUDGETPILOT_ENABLE_PAYPAL_SANDBOX") == "1",
    order_created=bool(st.session_state.get("checkout_order_result")),
    payment_verified=bool(st.session_state.get("bp_payment_verified")),
)
render_shopping_dashboard(
    summary,
    people=active_request.get("people") if active_request else None,
)
