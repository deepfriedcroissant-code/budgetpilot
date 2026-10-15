"""Payments team: replace demo checkout with PayPal sandbox Orders API."""
from uuid import uuid4

def create_order(approved_cart: list, catalog: dict) -> dict:
    from optimizer import calculate_total
    total = calculate_total(approved_cart, catalog)
    if total <= 0:
        raise ValueError('Empty cart')
    return {'order_id': 'DEMO-' + uuid4().hex[:8], 'status': 'SIMULATED', 'total': str(total), 'approval_url': None}
