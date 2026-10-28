"""Offline integration tests: Gemini/PayPal are deliberately not called."""
import unittest
from unittest.mock import patch

from main import build_cart, build_cart_from_request
from optimizer import calculate_total, recommend_cart
from validator import validate_request


class BackendWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "budget": 100.0,
            "people": 20,
            "categories": ["snacks", "drinks"],
            "priority": "variety",
        }

    def test_complete_request_to_cart_contract(self):
        with patch("main.parse_request", return_value=self.request) as mock_parser:
            request, cart, catalog = build_cart("snacks for a group under $100")
        mock_parser.assert_called_once()
        self.assertEqual(request, self.request)
        self.assertGreaterEqual(len(catalog), 30)
        self.assertTrue(cart)
        self.assertLessEqual(calculate_total(cart, catalog), self.request["budget"])
        for item in cart:
            self.assertIn(item["id"], catalog)
            self.assertIn(catalog[item["id"]]["category"], request["categories"])
            self.assertLessEqual(item["quantity"], catalog[item["id"]]["stock"])

    def test_optional_people_and_priority(self):
        request = dict(self.request, people=None, priority=None)
        self.assertTrue(validate_request(request))
        self.assertTrue(build_cart_from_request(request)[1])

    def test_missing_budget_is_rejected(self):
        request = dict(self.request, budget=None)
        with self.assertRaises(ValueError):
            build_cart_from_request(request)

    def test_unsupported_category_is_rejected(self):
        request = dict(self.request, categories=["imaginary"])
        with self.assertRaises(ValueError):
            build_cart_from_request(request)

    def test_out_of_stock_product_is_not_selected(self):
        stock = {
            "chips": {"category": "snacks", "price": "1.50", "stock": 0},
            "cookies": {"category": "snacks", "price": "2.00", "stock": 2},
        }
        snack_request = dict(self.request, categories=["snacks"])
        self.assertEqual(recommend_cart(snack_request, stock),
                         [{"id": "cookies", "quantity": 1}])

    def test_cart_rejects_stock_overrun(self):
        catalog = {"chips": {"category": "snacks", "price": "2.00", "stock": 2}}
        with self.assertRaises(ValueError):
            calculate_total([{"id": "chips", "quantity": 3}], catalog)

    def test_cart_rejects_duplicate_stock_overrun(self):
        catalog = {"chips": {"category": "snacks", "price": "2.00", "stock": 2}}
        cart = [{"id": "chips", "quantity": 2}, {"id": "chips", "quantity": 1}]
        with self.assertRaises(ValueError):
            calculate_total(cart, catalog)


if __name__ == "__main__":
    unittest.main()
