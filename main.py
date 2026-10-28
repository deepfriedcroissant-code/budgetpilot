"""Shared BudgetPilot backend contracts for Streamlit and offline testing."""
from catalog import load_catalog
from optimizer import calculate_total, recommend_cart
from parser import parse_request
from validator import validate_request


def build_cart_from_request(request: dict) -> tuple[dict, list, dict]:
    """Validate already parsed intent, load catalog, and recommend a cart."""
    validate_request(request)
    catalog = load_catalog()
    cart = recommend_cart(request, catalog)
    total = calculate_total(cart, catalog)
    if total > request["budget"]:
        raise ValueError("Optimizer returned an over-budget cart.")
    return request, cart, catalog


def build_cart(message: str) -> tuple[dict, list, dict]:
    """Live path: natural language -> Gemini -> validation -> catalog -> cart."""
    return build_cart_from_request(parse_request(message))


if __name__ == "__main__":
    # Offline smoke demo: no Gemini or PayPal account required.
    sample = {
        "budget": 100, "people": 20,
        "categories": ["snacks", "drinks"], "priority": "variety",
    }
    request, cart, catalog = build_cart_from_request(sample)
    print("Products available:", len(catalog))
    print("Request:", request)
    print("Cart:", cart)
    print("Total:", calculate_total(cart, catalog))
    print("For live Gemini tests, call build_cart(message) with an API key.")
