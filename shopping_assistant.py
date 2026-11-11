"""Explain recommendations and offer reviewable, deterministic budget repair.

These helpers use only the user's validated preferences and trusted catalog.
They never change a cart without an explicit click and never invoke PayPal.
"""
from decimal import Decimal, InvalidOperation

from optimizer import calculate_total


def explain_recommendation(product, request):
    """Provide a factual, catalog-grounded explanation, not invented LLM reasoning."""
    category = str(product.get("category", "")).replace("_", " ").lower()
    selected = set(request.get("categories") or [])
    reasons = []
    if product.get("category") in selected:
        reasons.append("matches your requested " + category + " category")
    priority = str(request.get("priority") or "variety").lower()
    if priority in {"budget", "price", "cheapest", "low_cost"}:
        reasons.append("was considered under your price-focused preference")
    else:
        reasons.append("adds another option to your suggested selection")
    if request.get("people"):
        reasons.append("was considered for your group shopping request")
    return "Selected because it " + ", and ".join(reasons) + "."


def suggest_budget_repair(cart, catalog, budget):
    """Reduce stock violations and expensive quantities until under budget.

    Returns a proposed cart plus a change log, without applying either.
    Preserve as many current units as possible by dropping the most expensive
    unit first. All prices come from the catalog; no replacement products are
    silently added. Raises when the input/catalog is invalid.
    """
    amount = Decimal(str(budget))
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Budget must be positive and finite.")
    quantities = {}
    changes = []
    for item in cart:
        if not isinstance(item, dict) or item.get("id") not in catalog:
            raise ValueError("Cart contains an unknown product.")
        pid, qty = item["id"], item.get("quantity")
        if type(qty) is not int or qty < 1:
            raise ValueError("Cart quantity is invalid.")
        quantities[pid] = quantities.get(pid, 0) + qty
    prices = {}
    for pid, qty in quantities.items():
        try:
            price = Decimal(str(catalog[pid]["price"]))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Catalog price is invalid.") from exc
        if not price.is_finite() or price <= 0:
            raise ValueError("Catalog price is invalid.")
        prices[pid] = price
        stock = catalog[pid].get("stock")
        if stock is not None:
            if type(stock) is not int or stock < 0:
                raise ValueError("Catalog stock is invalid.")
            if qty > stock:
                changes.append(f"Reduce {catalog[pid]['name']} from {qty} to {stock} (stock limit)")
                quantities[pid] = stock
    total = sum((prices[pid] * qty for pid, qty in quantities.items()), Decimal("0"))
    # Each step removes one expensive unit. No unbounded iteration over budget.
    for pid in sorted(quantities, key=lambda k: (-prices[k], str(k))):
        if total <= amount:
            break
        qty = quantities[pid]
        if qty <= 0:
            continue
        needed = int((total - amount) / prices[pid])
        if Decimal(needed) * prices[pid] < total - amount:
            needed += 1
        removed = min(qty, needed)
        quantities[pid] -= removed
        total -= prices[pid] * removed
        if removed:
            changes.append(f"Reduce {catalog[pid]['name']} by {removed}")
    proposed = [{"id": pid, "quantity": qty} for pid, qty in quantities.items() if qty > 0]
    if not proposed:
        return [], changes
    # Reuse the existing trusted stock and pricing validation.
    if calculate_total(proposed, catalog) > amount:
        raise ValueError("Could not prepare a cart within your budget.")
    return proposed, changes
