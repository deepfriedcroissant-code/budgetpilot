"""Pure contract tests for combined frontend integration.

No real Gemini/PayPal calls are performed.
"""
from decimal import Decimal

from catalog import load_catalog
from optimizer import calculate_total, recommend_cart
from validator import validate_request
from ui.product_display import build_rows


def test_combined_frontend_contract():
    request = {"budget": 100.0, "people": 20, "categories": ["snacks", "drinks"], "priority": "variety"}
    assert validate_request(request)
    catalog = load_catalog()
    cart = recommend_cart(request, catalog)
    assert cart
    assert calculate_total(cart, catalog) <= Decimal("100")
    rows, unknown = build_rows(cart, catalog)
    assert not unknown
    assert len(rows) == len(cart)
    assert all(r["stock"] is not None and r["unit_price"] is not None for r in rows)
