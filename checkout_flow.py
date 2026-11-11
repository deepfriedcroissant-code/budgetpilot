"""Persist and verify PayPal Sandbox approval/capture across Streamlit sessions.

Only orders created by BudgetPilot and saved here can be captured after redirect.
Local SQLite is suitable for one-machine demos, not distributed production hosting.
"""
import os
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent / ".budgetpilot" / "checkout.sqlite3"


def _connect(db_path=None):
    path = Path(db_path) if db_path is not None else Path(os.getenv("BUDGETPILOT_CHECKOUT_DB", str(DEFAULT_DB)))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS sandbox_orders (
        order_id TEXT PRIMARY KEY,
        return_state TEXT NOT NULL UNIQUE,
        amount TEXT NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'CREATED',
        capture_id TEXT
    )""")
    conn.commit()
    return conn


def _money(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Invalid order amount.")
        return f"{amount:.2f}"
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid order amount.") from exc


def record_order(order, db_path=None):
    """Call only after PayPal actually created an order with an approval URL."""
    order_id = order.get("order_id")
    state = order.get("return_state")
    if not isinstance(order_id, str) or not order_id or not isinstance(state, str) or len(state) < 24:
        raise ValueError("PayPal response is missing the order ID or return-state token.")
    if not order.get("approval_url"):
        raise ValueError("PayPal did not supply an approval URL.")
    amount = _money(order.get("total"))
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sandbox_orders(order_id,return_state,amount,currency,status) VALUES (?,?,?,?,?)",
            (order_id, state, amount, "USD", "CREATED"),
        )


def get_order(order_id, state, db_path=None):
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM sandbox_orders WHERE order_id=? AND return_state=?",
            (order_id, state),
        ).fetchone()
    return dict(row) if row is not None else None


def _record_capture_result(order_id, row, captured, db_path=None):
    """Verify identity, trusted price and currency before recording PayPal state."""
    if captured.get("order_id") != order_id:
        raise ValueError("PayPal order ID mismatch.")
    capture_id = captured.get("capture_id")
    if not capture_id:
        raise ValueError("PayPal response has no capture ID.")
    if _money(captured.get("total")) != row["amount"] or captured.get("currency") != row["currency"]:
        raise ValueError("PayPal capture amount/currency mismatch.")
    if row["capture_id"] and row["capture_id"] != capture_id:
        raise ValueError("Capture ID changed unexpectedly; manual review required.")
    status = str(captured.get("status") or "").upper()
    if status not in {"COMPLETED", "PENDING", "DECLINED", "FAILED", "REFUNDED", "PARTIALLY_REFUNDED"}:
        raise ValueError("Unrecognized PayPal capture status; review required.")
    local_status = status if status in {"COMPLETED", "PENDING"} else "UNSUCCESSFUL"
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE sandbox_orders SET status=?, capture_id=? "
            "WHERE order_id=? AND status IN ('CAPTURING','PENDING')",
            (local_status, capture_id, order_id),
        )
    return {
        "order_id": order_id, "status": status, "total": row["amount"],
        "capture_id": capture_id, "reason": captured.get("reason"),
    }


def check_payment_status(order_id, state, lookup_fn, db_path=None):
    """Read-only PayPal reconciliation. Never sends another capture request.

    Requires the original unpredictable state token and a locally recorded
    order; the browser cannot ask about arbitrary PayPal orders.
    """
    if not order_id or not state:
        raise ValueError("Order ID and return state are required.")
    row = get_order(order_id, state, db_path)
    if row is None:
        raise ValueError("Order is not recognized by this BudgetPilot session.")
    if row["status"] == "CREATED":
        # No capture attempt has been initiated by this app; don't imply payment.
        return {"order_id": order_id, "status": "NOT_CAPTURED"}
    if row["status"] == "COMPLETED":
        return {"order_id": order_id, "status": "COMPLETED",
                "total": row["amount"], "capture_id": row["capture_id"]}
    if row["status"] not in {"CAPTURING", "PENDING", "UNSUCCESSFUL"}:
        raise ValueError("Unexpected stored order status.")
    observed = lookup_fn(order_id)
    if observed.get("status") == "NO_CAPTURE":
        return {"order_id": order_id, "status": "UNRESOLVED"}
    if row["status"] == "UNSUCCESSFUL":
        # Terminal failures must not be magically retried or overwritten.
        return {"order_id": order_id, "status": "UNSUCCESSFUL",
                "capture_id": row["capture_id"]}
    return _record_capture_result(order_id, row, observed, db_path)


def finalize_return(order_id, state, capture_fn, db_path=None):
    """Capture once only; pending is an explicit state, not a payment failure.

    Never automatically recaptures when the local state is CAPTURING/PENDING.
    Such orders are inspected separately with check_payment_status().
    """
    if not order_id or not state:
        raise ValueError("Missing PayPal return token or checkout state.")
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM sandbox_orders WHERE order_id=? AND return_state=?",
            (order_id, state),
        ).fetchone()
        if row is None:
            raise ValueError("Unrecognized PayPal order or invalid return state.")
        if row["status"] == "COMPLETED":
            return {"order_id": order_id, "status": "COMPLETED", "total": row["amount"],
                    "capture_id": row["capture_id"], "already_verified": True}
        if row["status"] != "CREATED":
            raise ValueError("This order was already submitted for capture. Check Sandbox order status before retrying.")
        updated = conn.execute(
            "UPDATE sandbox_orders SET status='CAPTURING' "
            "WHERE order_id=? AND return_state=? AND status='CREATED'",
            (order_id, state),
        )
        if updated.rowcount != 1:
            raise ValueError("Another checkout request is processing this order.")
    # External network call after persistent CAPTURING marker guards retry.
    captured = capture_fn(order_id)
    return _record_capture_result(order_id, row, captured, db_path)
