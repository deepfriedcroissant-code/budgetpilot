"""Demo feature regressions: budget repair, explanations and verified checkout."""
from decimal import Decimal
from pathlib import Path
import pytest

from optimizer import calculate_total
from shopping_assistant import explain_recommendation, suggest_budget_repair

CATALOG = {
    "chips": {"id": "chips", "name": "Chips", "category": "snacks", "price": 4.50, "stock": 3},
    "juice": {"id": "juice", "name": "Juice", "category": "drinks", "price": 2.00, "stock": 4},
}


def test_explanation_grounded_in_request():
    text = explain_recommendation(CATALOG["chips"], {"categories": ["snacks"], "priority": "variety", "people": 5})
    assert "snacks" in text
    assert "group shopping request" in text
    assert "cheapest" not in text


def test_repair_preserves_original_and_proposes_affordable_cart():
    cart = [{"id": "chips", "quantity": 3}, {"id": "juice", "quantity": 2}]
    original = [dict(p) for p in cart]
    suggested, changes = suggest_budget_repair(cart, CATALOG, 9)
    assert cart == original
    assert changes
    assert suggested
    assert calculate_total(suggested, CATALOG) <= Decimal("9")
    assert {p["id"] for p in suggested} <= {"chips", "juice"}


def test_repair_cuts_stock_violations_and_never_increases_quantities():
    cart = [{"id": "chips", "quantity": 5}, {"id": "juice", "quantity": 1}]
    proposed, changes = suggest_budget_repair(cart, CATALOG, 100)
    assert proposed[0]["quantity"] == 3
    assert any("stock limit" in change for change in changes)


def test_repair_can_return_empty_for_too_small_budget():
    proposed, changes = suggest_budget_repair(
        [{"id": "chips", "quantity": 1}], CATALOG, .25
    )
    assert proposed == [] and changes


def test_repair_rejects_unknown_items():
    with pytest.raises(ValueError):
        suggest_budget_repair([{"id": "unknown", "quantity": 1}], CATALOG, 5)


def test_confirmation_requires_verified_result_and_no_mock_payment():
    source = (Path(__file__).parents[1] / "ui" / "order_confirmation.py").read_text()
    assert 'result.get("status") != "COMPLETED"' in source
    assert 'result.get("capture_id")' in source
    app = (Path(__file__).parents[1] / "app.py").read_text()
    assert 'finalize_return(token, state, capture_order)' in app
    assert 'st.session_state.bp_verified_receipt = result' in app
    assert 'render_verified_confirmation(st.session_state.bp_verified_receipt)' in app
    assert "st.stop()" in app


def test_ui_budget_repair_requires_explicit_apply_and_keeps_cart_checks():
    app = (Path(__file__).parents[1] / "app.py").read_text()
    assert '"Apply suggested changes", type="secondary"' in app
    assert 'on_click=_apply_suggested_cart' in app
    assert 'if edited and not valid:' in app
    assert 'reset_cart_validation=False' in app
    assert 'request=request' in app


def test_reduced_motion_covers_payment_success_animation():
    from ui.theme import STYLES
    assert ".bp-success-icon { animation:none; }" in STYLES


def test_product_card_renderer_receives_catalog_for_explanations():
    import ast
    source = (Path(__file__).parents[1] / "ui" / "product_display.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(node for node in tree.body
              if isinstance(node, ast.FunctionDef) and node.name == "_render_cards")
    assert "catalog" in [arg.arg for arg in fn.args.args]
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "_render_cards"]
    assert calls
    assert all("catalog" in [kw.arg for kw in call.keywords] for call in calls)
