import sys
from pathlib import Path

# Tell Python to look in the parent folder (budgetpilot/) for paypal_api.py
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
import hashlib
import json
import streamlit as st
from paypal_api import create_order
from checkout_flow import record_order


def _cart_fingerprint(cart: list[dict], budget: float | None, cart_version: int) -> str:
    """Generate a hash of the current cart and budget to detect any user edits."""
    normalized = sorted(
        [
            {"id": str(item.get("id", "")), "quantity": int(item.get("quantity", 0))}
            for item in (cart or [])
            if int(item.get("quantity", 0)) > 0
        ],
        key=lambda x: x["id"],
    )
    payload = {"cart": normalized, "budget": budget, "cart_version": cart_version}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def render_checkout(
    cart: list[dict],
    catalog: dict | list,
    budget: float | None = None,
    cart_valid: bool = True,
    cart_version: int = 0,
) -> dict | None:
    """
    Renders the Cart Approval and PayPal Sandbox Checkout section.
    Returns the created order dictionary if an order has been created for the current cart, else None.
    """
    st.subheader("Review & pay")

    # Filter out removed / 0-quantity items
    active_cart = [
        item for item in (cart or [])
        if isinstance(item.get("quantity"), int) and item.get("quantity", 0) > 0
    ]

    if not active_cart:
        st.info("Your cart is empty. Add items above before proceeding to checkout.")
        st.session_state.pop("checkout_order_result", None)
        st.session_state.pop("checkout_error", None)
        return None

    # Detect if the cart or recommendation version changed since last render
    current_fp = _cart_fingerprint(active_cart, budget, cart_version)
    previous_fp = st.session_state.get("checkout_cart_fp")

    if previous_fp != current_fp:
        st.session_state["checkout_cart_fp"] = current_fp
        # Cart changed: invalidate previous order results and errors
        st.session_state.pop("checkout_order_result", None)
        st.session_state.pop("checkout_error", None)

    # Block checkout if Group B's editable cart flagged budget or stock violations
    if not cart_valid:
        st.warning(
            "Cannot proceed to checkout: please resolve the budget or stock warnings in your cart above."
        )
        st.session_state.pop("checkout_order_result", None)
        return None

    # Dynamic key tied to current_fp ensures checkbox automatically resets when cart is edited
    approval_key = f"checkout_approved_{current_fp}"
    is_approved = st.checkbox(
        "I have reviewed my cart and agree to the displayed total",
        key=approval_key,
    )

    existing_order = st.session_state.get("checkout_order_result")

    # Prevent duplicate orders: disable button if not approved OR if order already exists for this cart
    button_disabled = (not is_approved) or (existing_order is not None)

    if st.button(
        "Continue to PayPal Sandbox",
        type="primary",
        disabled=button_disabled,
    ):
        st.session_state.pop("checkout_error", None)
        with st.spinner("Validating cart and creating PayPal Sandbox order..."):
            try:
                # Never bypass backend budget/stock validation.
                order_data = create_order(active_cart, catalog, budget=budget)
                # Store the trusted order/nonce on disk before sending the buyer to PayPal.
                # Streamlit may create a new browser session when PayPal redirects back.
                record_order(order_data)
                st.session_state["checkout_order_result"] = order_data
                existing_order = order_data
            except Exception as exc:
                st.session_state["checkout_error"] = str(exc)
                st.session_state.pop("checkout_order_result", None)
                existing_order = None

    # Show API or validation errors cleanly without crashing the app
    if "checkout_error" in st.session_state:
        st.error(f"Checkout failed: {st.session_state['checkout_error']}")

    # Display order result if created
    if existing_order:
        is_simulated = bool(
            existing_order.get("simulated")
            or str(existing_order.get("status", "")).upper() == "SIMULATED"
            or str(existing_order.get("order_id", "")).startswith("SIM-")
        )

        if is_simulated:
            st.warning(
                "**Simulated PayPal Order (Mock Mode)** — PayPal Sandbox credentials were not found in `.env`, so this order is simulated."
            )
        else:
            st.success("**Your checkout is ready**")

        col1, col2, col3 = st.columns(3)
        col1.metric("Order ID", existing_order.get("order_id", "N/A"))
        col2.metric("Status", existing_order.get("status", "CREATED"))
        col3.metric("Validated Total", f"${existing_order.get('total', '0.00')}")

        approval_url = existing_order.get("approval_url")
        if approval_url:
            if hasattr(st, "link_button"):
                st.link_button("Continue securely with PayPal Sandbox", approval_url)
            else:
                st.markdown(f"**[Continue with PayPal Sandbox]({approval_url})**")
            st.caption("You will return to BudgetPilot after approving in PayPal Sandbox.")

        st.info(
            "**Note:** Order creation is not payment. Only a verified PayPal capture confirms completion. "
            "Edit any item quantity above if you wish to modify your cart and create a new order."
        )

    return existing_order



#TESTER
if __name__ == "__main__":
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx() is None:
        import sys
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    else:
        # Running inside Streamlit browser -> show standalone test harness
        st.title("Checkout Component Standalone Preview")
        sample_catalog = {
            "snack_01": {"id": "snack_01", "name": "Party Size Tortilla Chips", "category": "snacks", "price": 4.50, "stock": 20},
            "drink_01": {"id": "drink_01", "name": "Sparkling Water 12-Pack", "category": "drinks", "price": 6.00, "stock": 10},
        }
        qty = st.number_input("Test Chips Quantity (change to test approval reset)", min_value=1, max_value=25, value=2)
        sample_cart = [
            {"id": "snack_01", "quantity": int(qty)},
            {"id": "drink_01", "quantity": 1},
        ]
        render_checkout(cart=sample_cart, catalog=sample_catalog, budget=50.0, cart_valid=True, cart_version=1)