"""Integration team: shared function contracts live here."""
import json
from pathlib import Path
from parser import parse_request
from optimizer import recommend_cart, calculate_total
from paypal_api import create_order

def load_catalog() -> dict:
    return json.loads((Path(__file__).parent / 'data' / 'products.json').read_text())

def build_cart(message: str) -> tuple[dict, list, dict]:
    catalog = load_catalog()
    request = parse_request(message)
    cart = recommend_cart(request, catalog)
    return request, cart, catalog

if __name__ == '__main__':
    request, cart, catalog = build_cart('Snacks and drinks for 10 people under $50')
    print('Request:', request)
    print('Cart:', cart)
    print('Total:', calculate_total(cart, catalog))
    print('Demo checkout:', create_order(cart, catalog))
