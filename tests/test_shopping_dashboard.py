"""Dynamic shopping sidebar contract tests; no network or Streamlit runtime."""
from decimal import Decimal

from ui.shopping_dashboard import build_sidebar_summary


CATALOG = {
    "chips": {"id": "chips", "price": Decimal("3.50"), "stock": 4},
    "juice": {"id": "juice", "price": Decimal("2.00"), "stock": 5},
}
REQUEST = {"budget": 10, "people": 3}


def summarize(cart, *, valid=True, order=False, payment=False):
    return build_sidebar_summary(
        REQUEST, cart, CATALOG, valid, True,
        order_created=order, payment_verified=payment,
    )


def test_sidebar_before_request_shows_empty_journey():
    summary = build_sidebar_summary(None, [], None, False, True)
    assert summary["stage"] == 0
    assert summary["has_request"] is False


def test_sidebar_uses_current_quantities_and_catalog_prices():
    data = summarize([{"id": "chips", "quantity": 2},
                      {"id": "juice", "quantity": 1}])
    assert data["total"] == Decimal("9.00")
    assert data["remaining"] == Decimal("1.00")
    assert data["percent"] == Decimal("90.0")
    assert data["units"] == 3 and data["products"] == 2
    assert data["cart_valid"] is True
    assert data["stage"] == 3


def test_over_budget_summary_updates_and_blocks_payment():
    data = summarize([{"id": "chips", "quantity": 3}], valid=False)
    assert data["total"] == Decimal("10.50")
    assert data["remaining"] == Decimal("-0.50")
    assert data["percent"] == Decimal("105.00")
    assert data["over_budget"] is True
    assert data["cart_valid"] is False


def test_recovery_from_over_budget_updates_live_metrics():
    over = summarize([{"id": "chips", "quantity": 3}], valid=False)
    within = summarize([{"id": "chips", "quantity": 2}], valid=True)
    assert over["cart_valid"] is False
    assert within["cart_valid"] is True
    assert within["remaining"] == Decimal("3.00")
    assert within["stage"] == 3


def test_overstock_does_not_hide_total_or_enable_payment():
    data = summarize([{"id": "chips", "quantity": 5}], valid=False)
    assert data["total"] == Decimal("17.50")
    assert data["cart_valid"] is False


def test_invalid_catalog_row_fails_closed():
    data = summarize([{"id": "unknown", "quantity": 1}], valid=True)
    assert data["cart_valid"] is False


def test_progress_only_completes_after_verified_capture():
    cart = [{"id": "chips", "quantity": 1}]
    assert summarize(cart, order=True)["stage"] == 4
    assert summarize(cart, payment=True)["stage"] == 5


def test_app_renders_sidebar_after_cart_editor():
    from pathlib import Path
    app = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    assert app.index("edited = render_cart_display(") < app.index("render_shopping_dashboard(")
    assert 'reset_cart_validation=False' in app
