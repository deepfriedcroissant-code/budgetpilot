"""No-network tests for Gemini 3.8 Flash configuration."""
from parser import _generation_config


def test_gemini_38_flash_uses_low_thinking():
    config = _generation_config("gemini-3.8-flash")
    assert config["response_mime_type"] == "application/json"
    assert config["thinking_config"]["thinking_level"] == "low"
    assert config["max_output_tokens"] == 1024


def test_other_models_do_not_receive_unsupported_thinking_config():
    assert _generation_config("gemini-2.5-flash") == {
        "response_mime_type": "application/json"
    }
    assert _generation_config("custom-model") == {
        "response_mime_type": "application/json"
    }
