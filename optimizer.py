
"""BudgetPilot cart recommendation and pricing logic.

Recommends products based on the user's budget, requested categories,
group size, available stock, and shopping priority.
"""

from decimal import Decimal, InvalidOperation


def _get_eligible_products(request: dict, catalog: dict) -> list[dict]:
    """Return valid, in-stock products from the requested categories."""
    categories = set(request["categories"])
    eligible = []

    for product_id, product in catalog.items():
        if product["category"] not in categories:
            continue

        try:
            price = Decimal(str(product["price"]))
        except (InvalidOperation, TypeError, ValueError):
            continue

        if not price.is_finite() or price <= 0:
            continue

        stock = product.get("stock", 1)

        if stock is not None:
            try:
                stock = int(stock)
            except (TypeError, ValueError):
                continue

            if stock <= 0:
                continue

        eligible.append({
            "id": product_id,
            "price": price,
            "stock": stock,
        })

    return eligible


def _get_target_quantity(request: dict, product_count: int) -> int:
    """Estimate the total number of product units needed for the group."""
    people = request.get("people")

    if people is None:
        return product_count

    return max(1, int(people))


def _can_add_product(
    product: dict,
    quantity: int,
    remaining_budget: Decimal,
) -> bool:
    """Check whether another unit can be added within budget and stock."""
    if product["price"] > remaining_budget:
        return False

    stock = product["stock"]

    if stock is not None and quantity >= stock:
        return False

    return True


def _recommend_variety(
    products: list[dict],
    target_quantity: int,
    budget: Decimal,
) -> dict:
    """Spread product quantities across the available selection."""
    quantities = {product["id"]: 0 for product in products}
    remaining_budget = budget
    total_quantity = 0

    # Add one unit per product in each round to encourage variety.
    while total_quantity < target_quantity:
        added_product = False

        for product in products:
            product_id = product["id"]

            if not _can_add_product(
                product, quantities[product_id], remaining_budget
            ):
                continue

            quantities[product_id] += 1
            remaining_budget -= product["price"]
            total_quantity += 1
            added_product = True

            if total_quantity >= target_quantity:
                break

        # Stop when the budget or available stock prevents more additions.
        if not added_product:
            break

    return quantities


def _recommend_budget(
    products: list[dict],
    target_quantity: int,
    budget: Decimal,
) -> dict:
    """Favor affordable products while maintaining some variety."""
    quantities = {product["id"]: 0 for product in products}
    remaining_budget = budget
    total_quantity = 0

    # Sort products from cheapest to most expensive.
    affordable_products = sorted(
        products,
        key=lambda product: product["price"],
    )

    # Give each product a chance to receive one unit before another round.
    while total_quantity < target_quantity:
        added_product = False

        for product in affordable_products:
            product_id = product["id"]

            if not _can_add_product(
                product, quantities[product_id], remaining_budget
            ):
                continue

            quantities[product_id] += 1
            remaining_budget -= product["price"]
            total_quantity += 1
            added_product = True

            if total_quantity >= target_quantity:
                break

        # Stop if no product can be added within the remaining constraints.
        if not added_product:
            break

    return quantities


def recommend_cart(request: dict, catalog: dict) -> list[dict]:
    """Recommend a cart using budget, categories, group size, and priority.

    Variety is the default priority. Budget-related priorities favor
    cheaper products while maintaining product variety. The returned
    cart contains only product IDs and positive integer quantities.
    """
    budget = Decimal(str(request["budget"]))

    if not budget.is_finite() or budget <= 0:
        return []

    products = _get_eligible_products(request, catalog)

    if not products:
        return []

    target_quantity = _get_target_quantity(request, len(products))
    priority = str(request.get("priority") or "variety").strip().lower()

    if priority in {"budget", "price", "cheapest", "low_cost"}:
        quantities = _recommend_budget(
            products, target_quantity, budget
        )
    else:
        quantities = _recommend_variety(
            products, target_quantity, budget
        )

    cart = []

    for product in products:
        product_id = product["id"]
        quantity = quantities[product_id]

        if quantity > 0:
            cart.append({
                "id": product_id,
                "quantity": quantity,
            })

    return cart


def calculate_total(cart: list[dict], catalog: dict) -> Decimal:
    """Compute trusted catalog total; reject invalid IDs, quantities, and stock."""
    totals_by_id = {}
    total = Decimal("0.00")

    for item in cart:
        if not isinstance(item, dict):
            raise ValueError("Invalid cart item")

        product_id = item.get("id")
        quantity = item.get("quantity")

        if (
            product_id not in catalog
            or type(quantity) is not int
            or quantity < 1
        ):
            raise ValueError("Invalid cart item")

        totals_by_id[product_id] = (
            totals_by_id.get(product_id, 0) + quantity
        )

        stock = catalog[product_id].get("stock")

        if stock is not None and totals_by_id[product_id] > int(stock):
            raise ValueError("Cart quantity exceeds stock")

        total += Decimal(str(catalog[product_id]["price"])) * quantity

    return total.quantize(Decimal("0.01"))
