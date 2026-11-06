import sys
from decimal import Decimal
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ui.product_display import build_rows, format_price, format_stock, NOT_PROVIDED
 
CATALOG = {
    "water": {"name": "Water", "price": "7.99", "category": "drinks", "stock": 10},
    "chips": {"name": "Chips", "price": Decimal("9.99"), "category": "snacks"},  # no stock
    "gone":  {"name": "Gone", "price": 1.5, "category": "snacks", "stock": 0},
}
 
 
def test_details_come_from_catalog():
    rows, unknown = build_rows([{"id": "water", "quantity": 2}], CATALOG)
    assert unknown == []
    r = rows[0]
    assert (r["name"], r["category"], r["unit_price"], r["stock"], r["quantity"]) == \
        ("Water", "drinks", Decimal("7.99"), 10, 2)
 
 
def test_unknown_id_reported_not_displayed():
    rows, unknown = build_rows([{"id": "ghost", "quantity": 1}, {"id": "water", "quantity": 1}], CATALOG)
    assert unknown == ["ghost"] and [r["id"] for r in rows] == ["water"]
 
 
def test_missing_stock_shows_not_provided():
    rows, _ = build_rows([{"id": "chips", "quantity": 1}], CATALOG)
    assert rows[0]["stock"] is None and format_stock(None) == NOT_PROVIDED
    assert rows[0]["warnings"] == []
 
 
def test_stock_warnings():
    rows, _ = build_rows([{"id": "water", "quantity": 11}, {"id": "gone", "quantity": 1}], CATALOG)
    assert "exceeds" in rows[0]["warnings"][0]
    assert rows[1]["warnings"] == ["Out of stock."]
 
 
def test_formatting_and_merging():
    assert format_price(Decimal("1234.5")) == "$1,234.50" and format_price(None) == NOT_PROVIDED
    rows, _ = build_rows([{"id": "water", "quantity": 1}, {"id": "water", "quantity": 2}], CATALOG)
    assert len(rows) == 1 and rows[0]["quantity"] == 3
    assert build_rows([], CATALOG) == ([], [])
 