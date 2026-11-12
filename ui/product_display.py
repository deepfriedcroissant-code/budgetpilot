"""
Run the demo:  streamlit run ui/product_display.py
"""
from decimal import Decimal, InvalidOperation
from html import escape

NOT_PROVIDED = "Not provided"


# --------------------------------------------------------------------------
# Pure helpers (no Streamlit) - easy to unit test
# --------------------------------------------------------------------------
def _normalize_catalog(catalog):
    """Accept {id: product} or [product, ...] and return {id: product}."""
    if isinstance(catalog, dict):
        return catalog
    return {p["id"]: p for p in catalog}


def _to_decimal(value):
    """Convert price-like values to Decimal; return None if unusable."""
    if value is None or isinstance(value, bool):
        return None
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    return d if d.is_finite() and d >= 0 else None


def _to_stock(value):
    """Return stock as int, or None when not provided / invalid."""
    if value is None or isinstance(value, bool):
        return None
    try:
        stock = int(value)
    except (TypeError, ValueError):
        return None
    return stock if stock >= 0 else None


def format_price(price):
    """Decimal -> '$9.99'; None -> 'Not provided'."""
    return NOT_PROVIDED if price is None else f"${price:,.2f}"


def format_stock(stock):
    """int -> '120 in stock' / 'Out of stock'; None -> 'Not provided'."""
    if stock is None:
        return NOT_PROVIDED
    return "Out of stock" if stock == 0 else f"{stock:,} in stock"


def build_rows(cart, catalog):
    """Join cart items with trusted catalog details.

    Returns (rows, unknown_ids).
      rows        - one dict per cart item whose id exists in the catalog:
                    id, name, category, unit_price (Decimal|None),
                    stock (int|None), quantity, warnings (list[str])
      unknown_ids - ids not found in the catalog (never displayed as products)
    Quantities for the same id are merged.
    """
    catalog = _normalize_catalog(catalog)
    merged, unknown = {}, []
    for item in cart or []:
        pid = item.get("id")
        try:
            qty = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            qty = 0
        if pid not in catalog:
            if pid not in unknown:
                unknown.append(pid)
            continue
        merged[pid] = merged.get(pid, 0) + qty

    rows = []
    for pid, qty in merged.items():
        p = catalog[pid]
        price, stock = _to_decimal(p.get("price")), _to_stock(p.get("stock"))
        warnings = []
        if price is None:
            warnings.append("Price missing or invalid in catalog.")
        if stock == 0:
            warnings.append("Out of stock.")
        elif stock is not None and qty > stock:
            warnings.append(f"Quantity {qty} exceeds available stock ({stock}).")
        if qty <= 0:
            warnings.append("Quantity must be at least 1.")
        rows.append({
            "id": pid,
            "name": p.get("name") or pid,
            "category": p.get("category") or NOT_PROVIDED,
            "unit_price": price,
            "stock": stock,
            "quantity": qty,
            "warnings": warnings,
        })
    return rows, unknown


# --------------------------------------------------------------------------
# Streamlit rendering
# --------------------------------------------------------------------------
def render_product_display(cart, catalog, layout="cards", show_quantity=True,
                           columns=3, request=None):
    """Render the recommended products. layout: 'cards' or 'table'.

    Returns the rows so app.py can reuse them. Display only: totals and
    payment amounts must still come from optimizer.calculate_total().
    """
    import streamlit as st

    st.subheader("Recommended products")
    rows, unknown = build_rows(cart, catalog)

    if not cart:
        st.info("No products recommended yet. Submit a request to generate a cart.")
        return rows

    for pid in unknown:
        st.error(f"Unknown product ID `{pid}`: not found in the product catalog, "
                 "so it can't be shown or purchased.")

    if not rows:
        return rows

    if any(r["stock"] is None for r in rows):
        st.caption("Stock levels not provided in the catalog for some items.")

    if layout == "table":
        _render_table(st, rows, show_quantity)
    else:
        _render_cards(st, rows, show_quantity, columns, request=request, catalog=_normalize_catalog(catalog))
    return rows


def _render_cards(st, rows, show_quantity, columns, request=None, catalog=None):
    for start in range(0, len(rows), columns):
        cols = st.columns(columns)
        for col, row in zip(cols, rows[start:start + columns]):
            with col, st.container(border=True):
                from ui.theme import product_icon
                icon = product_icon(row)
                name = escape(str(row["name"]))
                category = escape(row["category"].replace("_", " ").title())
                st.markdown(
                    f'<div class="bp-thumb bp-pop" role="img" aria-label="{category} product">'
                    f'{icon}</div><div class="bp-product-name">{name}</div>'
                    f'<div class="bp-muted">{category}</div>'
                    f'<div class="bp-price">{format_price(row["unit_price"])}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f'{format_stock(row["stock"])} · {row["quantity"]} in your cart' if show_quantity
                           else format_stock(row["stock"]))
                if request is not None:
                    from shopping_assistant import explain_recommendation
                    with st.expander("Why this pick?"):
                        st.caption(explain_recommendation(catalog[row["id"]], request))
                for w in row["warnings"]:
                    st.warning(w)


def _render_table(st, rows, show_quantity):
    table = []
    for r in rows:
        line = {
            "Product": r["name"],
            "Category": r["category"].replace("_", " ").title(),
            "Unit price": format_price(r["unit_price"]),
            "Stock": format_stock(r["stock"]),
        }
        if show_quantity:
            line["Qty"] = r["quantity"]
        line["Notes"] = " ".join(r["warnings"])
        table.append(line)
    st.dataframe(table, hide_index=True)
    for r in rows:
        for w in r["warnings"]:
            st.warning(f"{r['name']}: {w}")


# --------------------------------------------------------------------------
# Standalone demo:  streamlit run ui/product_display.py
# --------------------------------------------------------------------------
def _load_catalog_for_demo():
    """Prefer catalog.py; fall back to main.load_catalog() (per assignment)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from catalog import load_catalog
    except ImportError:
        from main import load_catalog
    return load_catalog()


def _demo():
    import streamlit as st
    st.set_page_config(page_title="Product display demo", layout="wide")
    st.title("Product display demo")
    catalog = _load_catalog_for_demo()

    sample_cart = [
        {"id": "salted_chips", "quantity": 4},
        {"id": "cookies", "quantity": 3},
        {"id": "water", "quantity": 5},
        {"id": "cola", "quantity": 2},
        {"id": "paper_plates", "quantity": 2},
        {"id": "not_a_real_item", "quantity": 1},   # unknown ID -> error message
    ]
    layout = st.radio("Layout", ["cards", "table"], horizontal=True)
    render_product_display(sample_cart, catalog, layout=layout)

    st.divider()
    st.caption("Same cart against a catalog with no stock field:")
    no_stock = {k: {x: v for x, v in p.items() if x != "stock"}
                for k, p in catalog.items()}
    render_product_display(sample_cart[:3], no_stock, layout="table")


if __name__ == "__main__":
    _demo()