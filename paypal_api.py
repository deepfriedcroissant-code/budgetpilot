import os
from decimal import Decimal, ROUND_HALF_UP
import requests
from dotenv import load_dotenv

# Load PayPal Sandbox credentials from .env
load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

def _normalize_catalog(catalog) -> dict:
    """
    Helper to support both dict-keyed catalogs {'p1': {...}}
    and list-based catalogs [{'id': 'p1', ...}] from catalog.py.
    """
    if isinstance(catalog, dict):
        # Check if someone wrapped the list inside {"products": [...]}
        if "products" in catalog and isinstance(catalog["products"], list):
            return {str(item["id"]): item for item in catalog["products"]}
        return {str(k): v for k, v in catalog.items()}
    elif isinstance(catalog, list):
        return {str(item["id"]): item for item in catalog}
    raise TypeError("Catalog must be a dict or a list of product dicts.")


def calculate_total(cart: list[dict], catalog) -> Decimal:
    """
    Shared Contract:
    calculate_total(cart, catalog) -> Decimal
    Computes the validated total using trusted catalog prices (never LLM prices).
    """
    if not cart:
        raise ValueError("Cannot calculate total for an empty cart.")

    catalog_map = _normalize_catalog(catalog)
    total = Decimal("0.00")

    for item in cart:
        product_id = str(item.get("id"))
        quantity = int(item.get("quantity", 0))

        if quantity <= 0:
            raise ValueError(f"Invalid quantity ({quantity}) for product ID '{product_id}'.")
        if product_id not in catalog_map:
            raise KeyError(f"Product ID '{product_id}' not found in trusted catalog.")

        # Always fetch price from the trusted catalog
        raw_price = catalog_map[product_id]["price"]
        unit_price = Decimal(str(raw_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += unit_price * quantity

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_access_token() -> str:
    """
    Authenticates with PayPal Sandbox OAuth2 API using .env credentials
    and returns a Bearer access token.
    """
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise EnvironmentError(
            "Missing PayPal credentials! Ensure PAYPAL_CLIENT_ID and "
            "PAYPAL_CLIENT_SECRET are set in your .env file."
        )

    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"PayPal Auth Failed ({response.status_code}): {response.text}"
        )

    return response.json()["access_token"]


def create_order(approved_cart: list[dict], catalog, currency: str = "USD") -> dict:
    """
    Shared Contract:
    create_order(approved_cart, catalog) -> dict: {order_id, status, total, approval_url}
    Creates a PayPal Sandbox order with itemized breakdown and returns the approval link.
    """
    catalog_map = _normalize_catalog(catalog)
    validated_total = calculate_total(approved_cart, catalog_map)
    access_token = get_access_token()

    # Build itemized breakdown for PayPal Orders v2 API
    paypal_items = []
    for cart_item in approved_cart:
        pid = str(cart_item["id"])
        qty = int(cart_item["quantity"])
        product = catalog_map[pid]
        unit_price = Decimal(str(product["price"])).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        paypal_items.append(
            {
                "name": product.get("name", f"Product {pid}")[:127],
                "quantity": str(qty),
                "unit_amount": {
                    "currency_code": currency,
                    "value": f"{unit_price:.2f}",
                },
            }
        )

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "description": "BudgetPilot AI-Assisted Shopping Order",
                "amount": {
                    "currency_code": currency,
                    "value": f"{validated_total:.2f}",
                    "breakdown": {
                        "item_total": {
                            "currency_code": currency,
                            "value": f"{validated_total:.2f}",
                        }
                    },
                },
                "items": paypal_items,
            }
        ],
        "application_context": {
            "brand_name": "BudgetPilot",
            "user_action": "PAY_NOW",
            "return_url": f"{APP_URL}/?payment=success",
            "cancel_url": f"{APP_URL}/?payment=cancelled",
        },
    }

    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=15)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"PayPal Order Creation Failed ({response.status_code}): {response.text}"
        )

    data = response.json()

    # Extract the buyer approval URL from HATEOAS links
    approval_url = None
    for link in data.get("links", []):
        if link.get("rel") in ("approve", "payer-action"):
            approval_url = link.get("href")
            break

    return {
        "order_id": data.get("id"),
        "status": data.get("status"),
        "total": str(validated_total),
        "approval_url": approval_url,
    }


def capture_order(order_id: str) -> dict:
    """
    Bonus helper for Week 3 (Oct 28 - Nov 3):
    Captures payment for an order after the buyer clicks 'Approve' on the approval_url.
    """
    access_token = get_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(url, headers=headers, timeout=15)
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"PayPal Order Capture Failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    return {
        "order_id": data.get("id"),
        "status": data.get("status"),
    }


# =====================================================================
# STANDALONE TEST BLOCK (Run `python paypal_api.py` to test your part!)
# =====================================================================
if __name__ == "__main__":
    print("--- Running BudgetPilot PayPal Sandbox Standalone Test ---")

    # 1. Sample trusted catalog (mimics data/products.json)
    sample_catalog = {
        "snack_01": {"id": "snack_01", "name": "Party Size Tortilla Chips", "category": "snacks", "price": 4.50, "stock": 20},
        "snack_02": {"id": "snack_02", "name": "Roasted Salsa Jar", "category": "snacks", "price": 3.75, "stock": 15},
        "drink_01": {"id": "drink_01", "name": "Sparkling Water 12-Pack", "category": "drinks", "price": 6.00, "stock": 10},
    }

    # 2. Sample approved cart (mimics optimizer.py output)
    sample_cart = [
        {"id": "snack_01", "quantity": 4},  # 4 * $4.50 = $18.00
        {"id": "snack_02", "quantity": 3},  # 3 * $3.75 = $11.25
        {"id": "drink_01", "quantity": 2},  # 2 * $6.00 = $12.00
    ]

    try:
        # Step A: Verify local calculation contract
        calculated = calculate_total(sample_cart, sample_catalog)
        print(f"[1/2] Validated Cart Total: ${calculated} (Expected: $41.25)")

        # Step B: Create PayPal Sandbox Order
        print("[2/2] Connecting to PayPal Sandbox API...")
        order_result = create_order(sample_cart, sample_catalog)

        print("\n✅ SUCCESS! PayPal Sandbox Order Created:")
        print(f"  • Order ID     : {order_result['order_id']}")
        print(f"  • Status       : {order_result['status']}")
        print(f"  • Total Charged: ${order_result['total']}")
        print(f"  • Approval URL : {order_result['approval_url']}")
        print("\n👉 Open the Approval URL in your browser and log in with a PayPal Sandbox Buyer account to test the checkout screen!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")