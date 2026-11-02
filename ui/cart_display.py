
"""Editable shopping cart, budget summary, and constraint feedback."""

from decimal import Decimal, InvalidOperation

import streamlit as st

from optimizer import calculate_total


def _remove_item(quantity_key: str) -> None:
    """Set an item's quantity to zero so it is removed on the next rerun."""
    st.session_state[quantity_key] = 0


def render_cart_display(
    cart: list[dict],
    catalog: dict,
    budget: float,
    cart_version: int = 0,
) -> list[dict]:
    """Render an editable cart and return the updated {id, quantity} items.

    The caller is responsible for saving the returned cart and clearing stale
    checkout approval/order results when the cart changes.
    """
    st.subheader("Review your cart")

    edited_cart = []
    stock_violations = []
    invalid_items = False

    # Create a fresh set of quantity widget keys for each new recommendation.
    for item in cart:
        product_id = item.get("id")

        if product_id not in catalog:
            st.error(
                f"Unknown product ID: {product_id}. "
                "Generate a new cart before checkout."
            )
            edited_cart.append(dict(item))
            invalid_items = True
            continue

        product = catalog[product_id]
        quantity_key = f"cart_{cart_version}_{product_id}"
        remove_key = f"remove_{cart_version}_{product_id}"

        # Initialize the widget only once per cart version.
        if quantity_key not in st.session_state:
            st.session_state[quantity_key] = item.get("quantity", 1)

        st.markdown(f"**{product['name']}**")
        st.caption(
            f"Category: {product.get('category', 'Not provided')} "
            f"| Unit price: ${Decimal(str(product['price'])):.2f}"
        )

        quantity_col, remove_col = st.columns([3, 1])

        with quantity_col:
            quantity = st.number_input(
                "Quantity",
                min_value=0,
                step=1,
                key=quantity_key,
                help="Set quantity to zero to remove this item.",
            )

        with remove_col:
            st.write("")
            st.button(
                "Remove",
                key=remove_key,
                on_click=_remove_item,
                args=(quantity_key,),
            )

        # Zero means the user removed the product.
        if quantity > 0:
            edited_cart.append(
                {"id": product_id, "quantity": int(quantity)}
            )

        subtotal = Decimal(str(product["price"])) * int(quantity)
        st.write(f"Subtotal: ${subtotal:.2f}")

        stock = product.get("stock")

        if stock is None:
            st.caption("Available stock: Not provided")
        else:
            st.caption(f"Available stock: {stock}")

            if (
                isinstance(stock, int)
                and not isinstance(stock, bool)
                and int(quantity) > stock
            ):
                stock_violations.append(product["name"])
                st.warning(
                    f"Only {stock} units of {product['name']} "
                    "are available."
                )

        st.divider()

    # Calculate totals using trusted catalog prices.
    try:
        total = calculate_total(edited_cart, catalog)
    except (ValueError, KeyError, TypeError, InvalidOperation):
        st.error(
            "The cart contains invalid items. "
            "Generate a new cart before checkout."
        )
        st.session_state["budgetpilot_cart_valid"] = False
        return edited_cart

    try:
        budget_amount = Decimal(str(budget))
        if not budget_amount.is_finite() or budget_amount < 0:
            raise ValueError("Budget must be a finite, nonnegative amount.")
    except (ValueError, TypeError, InvalidOperation):
        st.error("The budget is invalid.")
        st.session_state["budgetpilot_cart_valid"] = False
        return edited_cart

    remaining = budget_amount - total

    st.subheader("Budget summary")

    total_col, remaining_col = st.columns(2)

    with total_col:
        st.metric("Cart total", f"${total:.2f}")

    with remaining_col:
        st.metric("Remaining budget", f"${remaining:.2f}")

    budget_exceeded = remaining < 0

    if budget_exceeded:
        st.warning(
            "Your cart exceeds your budget. Reduce quantities "
            "or remove products before checkout."
        )

    if not edited_cart:
        st.info("Your cart is empty. Generate recommendations to start again.")

    # Expose validation and change status for the future app.py integration.
    # The integration lead must use these flags to block checkout and clear
    # stale approval/order results when the edited cart changes.
    original_cart = [
        {"id": item.get("id"), "quantity": item.get("quantity")}
        for item in cart
    ]

    st.session_state["budgetpilot_cart_changed"] = (
        edited_cart != original_cart
    )

    st.session_state["budgetpilot_cart_valid"] = (
        bool(edited_cart)
        and not invalid_items
        and not budget_exceeded
        and not stock_violations
    )

    return edited_cart
