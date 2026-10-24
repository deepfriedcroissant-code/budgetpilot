"""Owner: Yashmit — editable quantities, totals, and constraint feedback."""
from decimal import Decimal
import streamlit as st
from optimizer import calculate_total


def render_cart_display(cart: list[dict], catalog: dict, budget: float,
                        cart_version: int = 0) -> list[dict]:
    """Return an edited cart; the caller owns session-state persistence.

    TODO (Yashmit): improve removal UX and add stock checks when the catalog
    supplies stock. Increment cart_version after every new recommendation so
    Streamlit creates fresh quantity widgets. Zero quantity removes an item.
    """
    st.subheader("Review your cart")
    edited_cart = []
    for item in cart:
        product_id = item["id"]
        if product_id not in catalog:
            st.error(f"Unknown product: {product_id}. Generate a new cart.")
            # Preserve unknown items so checkout validation cannot hide them.
            edited_cart.append(dict(item))
            continue
        product = catalog[product_id]
        quantity = int(st.number_input(
            f"Quantity — {product['name']}", min_value=0, step=1,
            value=item["quantity"], key=f"cart_{cart_version}_{product_id}",
        ))
        if quantity:
            edited_cart.append({"id": product_id, "quantity": quantity})
        st.write(f"Subtotal: ${Decimal(str(product['price'])) * quantity:.2f}")
        if product.get("stock") is not None and quantity > product["stock"]:
            st.warning(f"{product['name']} exceeds available stock.")
    try:
        total = calculate_total(edited_cart, catalog)
    except (ValueError, KeyError):
        st.error("The cart contains invalid items. Generate a new cart.")
        return edited_cart
    remaining = Decimal(str(budget)) - total
    st.metric("Cart total", f"${total:.2f}")
    st.metric("Remaining budget", f"${remaining:.2f}")
    if remaining < 0:
        st.warning("Your cart exceeds your budget. Reduce quantities before checkout.")
    return edited_cart
