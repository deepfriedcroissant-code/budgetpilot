"""Sandbox checkout regression tests: no external PayPal API calls."""
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import pytest

import paypal_api
from checkout_flow import finalize_return, get_order, record_order


def _order(state="a" * 40, amount="9.00"):
    return {
        "order_id": "ORDER-TEST",
        "return_state": state,
        "total": amount,
        "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-TEST",
    }


def _captured(order_id):
    return {
        "order_id": order_id,
        "status": "COMPLETED",
        "total": "9.00",
        "currency": "USD",
        "capture_id": "CAP-TEST",
    }


def test_verified_capture_and_duplicate_return_is_idempotent(tmp_path):
    db = tmp_path / "state.db"
    record_order(_order(), db)
    called = []
    def capture(order_id):
        called.append(order_id)
        return _captured(order_id)
    one = finalize_return("ORDER-TEST", "a" * 40, capture, db)
    two = finalize_return("ORDER-TEST", "a" * 40, capture, db)
    assert one["status"] == two["status"] == "COMPLETED"
    assert two["already_verified"] is True
    assert called == ["ORDER-TEST"]


def test_invalid_nonce_never_captures(tmp_path):
    db = tmp_path / "state.db"
    record_order(_order(), db)
    with pytest.raises(ValueError, match="invalid return state"):
        finalize_return("ORDER-TEST", "b" * 40, lambda _: pytest.fail("capture should not run"), db)


@pytest.mark.parametrize("total,currency,status", [
    ("10.00", "USD", "COMPLETED"),
    ("9.00", "EUR", "COMPLETED"),
    ("9.00", "USD", "PENDING"),
])
def test_unverified_capture_never_marks_complete(tmp_path, total, currency, status):
    db = tmp_path / "state.db"
    record_order(_order(), db)
    def capture(order_id):
        return {**_captured(order_id), "total": total, "currency": currency, "status": status}
    with pytest.raises(ValueError):
        finalize_return("ORDER-TEST", "a" * 40, capture, db)
    assert get_order("ORDER-TEST", "a" * 40, db)["status"] == "CAPTURING"
    with pytest.raises(ValueError, match="already submitted"):
        finalize_return("ORDER-TEST", "a" * 40, capture, db)


def test_unrecognized_order_never_captures(tmp_path):
    with pytest.raises(ValueError, match="Unrecognized"):
        finalize_return("FORGED", "a" * 40, lambda _: pytest.fail("capture should not run"), tmp_path / "db.sqlite")


def test_paypal_create_order_uses_stateful_redirect(monkeypatch):
    monkeypatch.setattr(paypal_api, "APP_URL", "http://localhost:8501")
    monkeypatch.setattr(paypal_api, "PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
    catalog = {"chips": {"id": "chips", "name": "Chips", "price": Decimal("3.00"), "stock": 4}}
    class Response:
        status_code = 201
        def json(self):
            return {"id": "ORDER-TEST", "status": "CREATED",
                    "links": [{"rel": "approve", "href": "https://www.sandbox.paypal.com/checkout"}]}
    with patch("paypal_api.get_access_token", return_value="FAKE"), patch(
        "paypal_api.requests.post", return_value=Response()
    ) as post:
        data = paypal_api.create_order([{"id": "chips", "quantity": 3}], catalog, budget=12)
    query = parse_qs(urlparse(post.call_args.kwargs["json"]["application_context"]["return_url"]).query)
    assert query["state"] == [data["return_state"]]
    assert query["payment"] == ["success"]
    assert len(data["return_state"]) >= 24


def test_capture_order_extracts_paypal_amount(monkeypatch):
    monkeypatch.setattr(paypal_api, "PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
    class Response:
        status_code = 201
        def json(self):
            return {"id": "ORDER-TEST", "status": "COMPLETED", "purchase_units": [{
                "payments": {"captures": [{"id": "CAP-TEST", "status": "COMPLETED",
                    "amount": {"value": "9.00", "currency_code": "USD"}}]}
            }]}
    with patch("paypal_api.get_access_token", return_value="FAKE"), patch(
        "paypal_api.requests.post", return_value=Response()
    ):
        result = paypal_api.capture_order("ORDER-TEST")
    assert result["total"] == "9.00"
    assert result["currency"] == "USD"
    assert result["capture_id"] == "CAP-TEST"


def test_production_paypal_blocked(monkeypatch):
    monkeypatch.setattr(paypal_api, "PAYPAL_BASE_URL", "https://api-m.paypal.com")
    with pytest.raises(RuntimeError, match="Sandbox"):
        paypal_api.get_access_token()
