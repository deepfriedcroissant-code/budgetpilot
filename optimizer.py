"""BudgetPilot's small, deterministic MVP cart recommendation algorithm.

Yashmit owns improved quantity/variety/people-based recommendations. This
integration baseline keeps the existing public function signatures unchanged.
"""
from decimal import Decimal


def recommend_cart(request: dict, catalog: dict) -> list[dict]:
    """Select affordable in-stock items in requested categories.

    MVP heuristic: one unit of each eligible item in catalog order. This is
    intentionally NOT serving-size or preference optimization yet.
    """
    remaining = Decimal(str(request["budget"]))
    categories = set(request["categories"])
    cart = []
    for product_id, product in catalog.items():
        if product["category"] not in categories:
            continue
        if int(product.get("stock", 1)) <= 0:
            continue
        price = Decimal(str(product["price"]))
        if price <= remaining:
            cart.append({"id": product_id, "quantity": 1})
            remaining -= price
    return cart


def calculate_total(cart: list[dict], catalog: dict) -> Decimal:
    """Compute trusted catalog total; reject invalid IDs, quantities, and stock."""
    totals_by_id = {}
    total = Decimal("0.00")
    for item in cart:
        if not isinstance(item, dict):
            raise ValueError("Invalid cart item")
        pid = item.get("id")
        qty = item.get("quantity")
        if pid not in catalog or type(qty) is not int or qty < 1:
            raise ValueError("Invalid cart item")
        totals_by_id[pid] = totals_by_id.get(pid, 0) + qty
        stock = catalog[pid].get("stock")
        if stock is not None and totals_by_id[pid] > int(stock):
            raise ValueError("Cart quantity exceeds stock")
        total += Decimal(str(catalog[pid]["price"])) * qty
    return total.quantize(Decimal("0.01"))
