"""PayPal contract tests with mocked HTTP, never creating actual orders."""
from unittest.mock import patch
from decimal import Decimal

import pytest

from paypal_api import calculate_total, create_order


CATALOG = {
    "chips": {"id": "chips", "name": "Chips", "price": Decimal("3.50"), "stock": 4},
    "juice": {"id": "juice", "name": "Juice", "price": Decimal("2.00"), "stock": 3},
}
CART = [{"id": "chips", "quantity": 2}, {"id": "juice", "quantity": 1}]


def test_trusted_cart_total():
    assert calculate_total(CART, CATALOG) == Decimal("9.00")


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", True])
def test_invalid_quantity_rejected(quantity):
    with pytest.raises(ValueError):
        calculate_total([{"id": "chips", "quantity": quantity}], CATALOG)


def test_cumulative_stock_limit():
    with pytest.raises(ValueError):
        calculate_total([
            {"id": "chips", "quantity": 3},
            {"id": "chips", "quantity": 2},
        ], CATALOG)


def test_budget_constraint_before_paypal():
    with pytest.raises(ValueError):
        create_order(CART, CATALOG, budget=8)


def test_create_order_payload_uses_catalog_prices():
    class FakeResponse:
        status_code = 201

        def json(self):
            return {
                "id": "TEST-ORDER", "status": "CREATED",
                "links": [{"rel": "approve", "href": "https://example.invalid/approve"}],
            }

    with patch("paypal_api.get_access_token", return_value="TEST-TOKEN"):
        with patch("paypal_api.requests.post", return_value=FakeResponse()) as post:
            order = create_order(CART, CATALOG, budget=10)
    assert order["order_id"] == "TEST-ORDER"
    assert order["total"] == "9.00"
    sent = post.call_args.kwargs["json"]
    assert sent["purchase_units"][0]["amount"]["value"] == "9.00"
