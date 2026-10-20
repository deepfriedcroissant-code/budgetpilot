import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent/"data"/"products.json"
REQUIRED_FIELDS = {"name", "category", "price", "stock"}
CATEGORIES = ["snacks", "drinks", "groceries", "party_supplies", "household", "health", "frozen"]

def load_catalog(path=DEFAULT_PATH) -> dict:
    """Return the catalog as {product_id: {id, name, category, price, stock}}"""

    with open(path, encoding = "utf-8") as f:
        raw = json.load(f)

    catalog = {}
    for pid, p in raw.items():
        # Invalid cases
        missing = REQUIRED_FIELDS - p.keys()
        if missing:
            raise ValueError(f"Product {pid} missing fields: {sorted(missing)}")
        try:
            price = Decimal(str(p["price"]))
        except InvalidOperation:
            raise ValueError(f"Invalid price for {pid}: {p['price']!r}")
        if price <= 0 or int(p["stock"]) < 0:
            raise ValueError(f"Invalid price/stock for {pid}")
        if p["category"] not in CATEGORIES:
            raise ValueError(f"Unknown category '{p['category']}' for {pid}")
        
        #Add validated product to the catalog
        catalog[pid] = {"id": pid, "name": p['name'], "category": p["category"],
                        "price": price, "stock": int(p["stock"])}
    return catalog

def load_product_list(path = DEFAULT_PATH) -> list:
    # same data as load_catalog() returned as a plain list
    return list(load_catalog(path).values())

def products_by_category(catalog: dict, category: str, in_stock_only=True) -> list:
    # order by cheapest first
    items = [p for p in catalog.values()
        if p["category"] == category and (p["stock"] > 0 or not in_stock_only)]
    return sorted(items, key=lambda p: p["price"])

if __name__ == "__main__":
    cat = load_catalog()
    print(f"Loaded {len(cat)} products")
    for c in CATEGORIES:
        print(f" {c:15s} {len(products_by_category(cat, c))}")