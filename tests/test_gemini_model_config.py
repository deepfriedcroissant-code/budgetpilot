"""No-network tests for active Gemini 3.1 Flash-Lite JSON configuration."""
from parser import _generation_config


def test_gemini_31_flash_lite_requests_json():
    assert _generation_config("gemini-3.1-flash-lite") == {
        "response_mime_type": "application/json"
    }


def test_other_models_do_not_receive_unnecessary_thinking_settings():
    for model in ("gemini-2.5-flash", "gemini-3.8-flash", "custom-model"):
        assert _generation_config(model) == {"response_mime_type": "application/json"}
