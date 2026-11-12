"""Live budget and checkout progress for the BudgetPilot sidebar.

All totals come from trusted catalog prices, never generated Gemini prices.
"""
from decimal import Decimal, InvalidOperation
import streamlit as st


def build_sidebar_summary(request, cart, catalog, cart_valid, checkout_enabled, order_created=False, payment_verified=False):
    """Pure, testable model used by the customer-facing shopping dashboard."""
    if not request or catalog is None:
        return {
            "has_request": False, "budget": Decimal("0"), "total": Decimal("0"),
            "remaining": Decimal("0"), "units": 0, "products": 0,
            "percent": 0, "over_budget": False, "cart_valid": False,
            "checkout_enabled": bool(checkout_enabled), "stage": 0,
        }
    try:
        budget = Decimal(str(request["budget"]))
        if not budget.is_finite() or budget <= 0:
            raise ValueError("Invalid shopping budget")
        active_cart = [p for p in (cart or []) if isinstance(p, dict) and
                       type(p.get("quantity")) is int and p["quantity"] > 0]
        # Display a trusted-price total even when stock is exceeded.
        # The editor's cart_valid flag still prevents checkout.
        total = Decimal("0")
        for item in active_cart:
            price = Decimal(str(catalog[item["id"]]["price"]))
            if not price.is_finite() or price <= 0:
                raise ValueError("Invalid catalog price")
            total += price * item["quantity"]
        products = len({str(item["id"]) for item in active_cart})
        units = sum(item["quantity"] for item in active_cart)
    except (ValueError, KeyError, TypeError, InvalidOperation):
        # Unexpected catalog or cart errors fail closed rather than displaying readiness.
        return {
            "has_request": True, "budget": Decimal("0"), "total": Decimal("0"),
            "remaining": Decimal("0"), "units": 0, "products": 0,
            "percent": 0, "over_budget": False, "cart_valid": False,
            "checkout_enabled": bool(checkout_enabled), "stage": 1,
        }
    remaining = budget - total
    percent = max(0, (total / budget) * 100)
    valid = bool(cart_valid) and bool(active_cart) and total <= budget
    stage = 5 if payment_verified else (4 if order_created else (3 if valid else (2 if active_cart else 1)))
    return {
        "has_request": True, "budget": budget, "total": total,
        "remaining": remaining, "units": units, "products": products,
        "percent": percent, "over_budget": total > budget,
        "cart_valid": valid, "checkout_enabled": bool(checkout_enabled),
        "stage": stage,
    }


def render_shopping_dashboard(summary, people=None):
    """Render after the cart editor to reflect quantities on the *current* rerun."""
    with st.sidebar:
        st.markdown("### Your shopping cart")
        if not summary["has_request"]:
            st.caption("Your personalized shopping overview will appear here.")
            st.markdown("**Your journey**")
            for label in ("Describe your needs", "Find your picks", "Review your cart", "Pay with PayPal"):
                st.caption("○  " + label)
            st.divider()
            st.caption("PayPal Sandbox · Demo payments only")
            return

        used = summary["percent"]
        over = summary["over_budget"]
        status = (
            "Over budget" if over
            else "Checkout complete" if summary["stage"] == 5
            else "Cart ready" if summary["cart_valid"]
            else "Review your cart"
        )
        status_class = "bp-status-alert" if over else ("bp-status-good" if summary["cart_valid"] or summary["stage"] == 5 else "bp-status-idle")
        st.markdown(
            f'<div class="bp-side-status {status_class}">{status}</div>',
            unsafe_allow_html=True,
        )
        st.caption("CART TOTAL / YOUR BUDGET")
        st.markdown(
            f'<div class="bp-side-total">${summary["total"]:,.2f}'
            f'<span> / ${summary["budget"]:,.2f}</span></div>',
            unsafe_allow_html=True,
        )
        # A native progress indicator updates with each Streamlit rerun.
        st.progress(min(1.0, float(used / 100)),
                    text=f"{used:.0f}% of your budget used")
        if over:
            st.error(f"${abs(summary['remaining']):,.2f} over budget")
        else:
            st.caption(f"${summary['remaining']:,.2f} remaining")

        a, b = st.columns(2)
        a.metric("Products", summary["products"])
        b.metric("Units", summary["units"])
        if people is not None:
            st.caption(f"Shopping for {people} people")

        st.divider()
        st.markdown("**Shopping progress**")
        labels = ("Request understood", "Recommendations ready",
                  "Cart reviewed", "PayPal approval")
        for index, label in enumerate(labels, 1):
            if index < summary["stage"]:
                mark = "✓"
                css = "bp-step-done"
            elif index == summary["stage"]:
                mark = "●"
                css = "bp-step-active"
            else:
                mark = "○"
                css = "bp-step-pending"
            st.markdown(
                f'<div class="bp-step-row {css}">'
                f'<span>{mark}</span><span>{label}</span></div>',
                unsafe_allow_html=True,
            )
        if not summary["checkout_enabled"]:
            st.caption("Checkout is unavailable in this session.")
        elif summary["stage"] == 5:
            st.caption("Sandbox checkout completed successfully.")
        elif summary["cart_valid"]:
            st.caption("Review the total below, then proceed to checkout.")
        else:
            st.caption("Adjust your quantities to continue.")
        st.divider()
        st.caption("PayPal Sandbox · Demo payments only")
