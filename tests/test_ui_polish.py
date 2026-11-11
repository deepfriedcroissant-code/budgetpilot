"""Customer-facing UI smoke checks without a browser or API requests."""
from pathlib import Path
from ui.theme import product_icon, STYLES


def test_product_tiles_have_relevant_safe_fallback():
    assert product_icon({"id": "cookies", "category": "snacks"}) == "🍪"
    assert product_icon({"id": "not_in_icons", "category": "drinks"}) == "🥤"
    assert product_icon({"id": "not_in_icons", "category": "unknown"}) == "🛍️"


def test_accessible_motion_fallback_is_present():
    assert "prefers-reduced-motion" in STYLES


def test_main_shopping_screen_omits_internal_integration_labels():
    code = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    for text in (
        "Integration status", "release candidate", "until checkout verification",
        "until payment-return and capture verification are tested",
        "Live Gemini requires GEMINI_API_KEY",
    ):
        assert text not in code
    assert "PayPal Sandbox" in code
