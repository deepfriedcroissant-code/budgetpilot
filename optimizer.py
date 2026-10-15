"""Recommendation team: implement budget-aware cart selection."""
from decimal import Decimal

def recommend_cart(request: dict, catalog: dict) -> list:
    remaining = Decimal(str(request['budget']))
    cart = []
    for product_id, product in catalog.items():
        if product['category'] not in request['categories']:
            continue
        price = Decimal(product['price'])
        if price <= remaining:
            cart.append({'id': product_id, 'quantity': 1})
            remaining -= price
    return cart

def calculate_total(cart: list, catalog: dict) -> Decimal:
    total = Decimal('0.00')
    for item in cart:
        if item['id'] not in catalog or type(item['quantity']) is not int or item['quantity'] < 1:
            raise ValueError('Invalid cart item')
        total += Decimal(catalog[item['id']]['price']) * item['quantity']
    return total.quantize(Decimal('0.01'))
