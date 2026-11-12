"""Checkout state regression tests without starting Streamlit."""
import ast
from pathlib import Path
from types import SimpleNamespace


def _load_clear_checkout_state(session_state):
    """Compile only the helper to avoid importing the full Streamlit app."""
    path = Path(__file__).parents[1] / "app.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    func = next(n for n in module.body
                if isinstance(n, ast.FunctionDef) and n.name == "_clear_checkout_state")
    namespace = {"st": SimpleNamespace(session_state=session_state)}
    exec(compile(ast.Module(body=[func], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["_clear_checkout_state"]


def test_cart_edit_preserves_latest_validity_and_resets_approval():
    state = {
        "budgetpilot_cart_valid": True,
        "budgetpilot_cart_changed": True,
        "checkout_approved_abc": True,
        "checkout_order_result": {"order_id": "OLD"},
        "checkout_error": "old error",
        "checkout_cart_fp": "abc",
    }
    _load_clear_checkout_state(state)(reset_cart_validation=False)
    assert state["budgetpilot_cart_valid"] is True
    assert state["budgetpilot_cart_changed"] is True
    assert not any(key.startswith("checkout_") for key in state)


def test_over_budget_edit_preserves_invalidity_and_clears_payment_state():
    state = {
        "budgetpilot_cart_valid": False,
        "checkout_approved_old": True,
        "checkout_order_result": {"order_id": "OLD"},
    }
    _load_clear_checkout_state(state)(reset_cart_validation=False)
    assert state == {"budgetpilot_cart_valid": False}


def test_new_shopping_request_resets_validation_and_payment_state():
    state = {"budgetpilot_cart_valid": True, "budgetpilot_cart_changed": True,
             "checkout_approved_old": True}
    _load_clear_checkout_state(state)()
    assert state == {}
