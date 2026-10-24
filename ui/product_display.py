"""Owner: Set — recommended product details from the trusted catalog."""
import streamlit as st


def render_product_display(cart: list[dict], catalog: dict) -> None:
    """Render products matching optimizer item IDs.

    Pass main.load_catalog() for now. TODO (Set): use catalog.py when it
    exists, improve layout, and agree on a stock field with Yashmit.
    Current data/products.json has no stock field; do not invent availability.
    """
    st.subheader("Recommended products")
    if not cart:
        st.info("No recommended products yet.")
        return
    for item in cart:
        product_id = item["id"]
        product = catalog.get(product_id)
        if product is None:
            st.warning(f"Product ID {product_id} was not found in the catalog.")
            continue
        st.write(f"**{product['name']}**")
        st.caption(f"ID: {product_id} · Category: {product['category']}")
        st.write(f"Unit price: ${product['price']}")
        st.write(f"Available stock: {product.get('stock', 'Not provided')}")
