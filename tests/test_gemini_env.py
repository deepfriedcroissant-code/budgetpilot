"""Tests for explicit Gemini .env loading (no real API requests)."""
import os
from pathlib import Path

import pytest
from parser import GeminiConfigurationError, _get_gemini_key


def test_missing_key_has_actionable_message(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("parser.Path", lambda x: tmp_path / "parser.py")
    with pytest.raises(GeminiConfigurationError, match="\.env"):
        _get_gemini_key()


def test_local_env_is_loaded(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("GEMINI_API_KEY=test_key_for_unit_testing\n")
    monkeypatch.setattr("parser.Path", lambda x: tmp_path / "parser.py")
    assert _get_gemini_key() == "test_key_for_unit_testing"


def test_environment_variable_takes_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "environment_key")
    (tmp_path / ".env").write_text("GEMINI_API_KEY=local_key\n")
    monkeypatch.setattr("parser.Path", lambda x: tmp_path / "parser.py")
    assert _get_gemini_key() == "environment_key"
