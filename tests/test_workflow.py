import unittest
from main import build_cart
from optimizer import calculate_total

class TestWorkflow(unittest.TestCase):
    def test_cart_within_budget(self):
        request, cart, catalog = build_cart('Snacks and drinks for 10 people under $50')
        self.assertLessEqual(calculate_total(cart, catalog), request['budget'])

if __name__ == '__main__':
    unittest.main()
