"""Gemini shopping-intent parser with explicit local .env support."""
import json
import os
import time
from pathlib import Path


class GeminiConfigurationError(RuntimeError):
    """Local Gemini configuration is missing or unusable."""


class GeminiRequestError(RuntimeError):
    """Gemini could not process the request; safe for the UI to display."""


def _get_gemini_key() -> str:
    """Load .env next to this file regardless of the VS Code working directory."""
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=False)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key.lower() in {
        "your_new_api_key_here", "your-gemini-api-key",
        "your_actual_gemini_key", "replace_me", "placeholder",
    }:
        raise GeminiConfigurationError(
            "Gemini API key is missing. Create a .env file next to app.py "
            "and set GEMINI_API_KEY to a valid, newly generated key."
        )
    return key


def _generation_config(model: str) -> dict:
    """Use a concise JSON response for shopping-intent extraction."""
    config = {"response_mime_type": "application/json"}
    return config


def parse_request(message: str) -> dict:
    """Extract shopping requirements: budget, people, categories, priority."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please enter a shopping request.")

    from catalog import CATEGORIES
    from google import genai

    key = _get_gemini_key()
    client = genai.Client(api_key=key)

    categories = ", ".join(CATEGORIES)
    prompt = (
        "You are BudgetPilot's shopping-intent interpreter. "
        "Return only a JSON object with EXACT keys: budget, people, categories, priority. "
        "budget must be a positive number or null if not given; "
        "people must be a positive integer or null if not given; "
        "categories must be a list using only these exact values: " + categories + ". "
        "Use [] if none are clear, and do not make up categories. "
        "priority should be a short string such as 'variety', 'budget', or null. "
        "Never invent prices, product IDs, budgets, or headcounts. "
        "Do not create a cart. Shopping request: " + message.strip()
    )

    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    start = time.perf_counter()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=_generation_config(model),
        )
    except Exception as exc:
        # Never surface provider exception strings or request headers:
        # some SDK exceptions can include sensitive request details.
        message_lower = str(exc).lower()
        code = str(getattr(exc, "code", "") or "")
        status = str(getattr(exc, "status", "") or "").lower()
        if code == "401" or "unauthenticated" in status or any(
            s in message_lower for s in ("api key not valid", "api_key_invalid", "invalid api key")
        ):
            explanation = "Gemini rejected the API key (401). Replace GEMINI_API_KEY in your local .env."
        elif code == "403" or "permission_denied" in status or "permission denied" in message_lower:
            explanation = "Gemini access denied (403). Check API-key restrictions and Gemini API permissions."
        elif code == "429" or "resource_exhausted" in status or any(
            s in message_lower for s in ("quota", "rate limit")
        ):
            explanation = "Gemini quota or rate limit reached (429). Check your Gemini API quota."
        elif code == "404" or "not_found" in status or any(
            s in message_lower for s in ("unsupported model", "model not available")
        ):
            explanation = f"Gemini model '{model}' was not found or is unavailable to this API key (404)."
        elif code == "400" or "invalid_argument" in status:
            explanation = "Gemini rejected the request (400). Check the model configuration and API settings."
        elif code in ("500", "502", "503", "504") or "unavailable" in status:
            explanation = f"Gemini service temporarily unavailable ({code or 'server error'}). Retry."
        elif any(s in message_lower for s in ("timeout", "timed out", "connection", "dns", "ssl", "certificate")):
            explanation = "Connection to Gemini failed. Check network, proxy, firewall, or certificates."
        else:
            explanation = (
                "Gemini request failed. Run 'python scripts/check_gemini.py' "
                "to diagnose the API key, model, and connection safely."
            )
        raise GeminiRequestError(explanation) from exc
    finally:
        # Only log the model and elapsed time; never log user requests or keys.
        print(f"Gemini API ({model}) took {time.perf_counter() - start:.2f} seconds")

    if not response.text:
        raise GeminiRequestError("Gemini returned an empty response. Please retry.")

    try:
        data = json.loads(response.text)
    except (TypeError, ValueError) as exc:
        raise GeminiRequestError("Gemini returned invalid JSON. Please retry.") from exc
    if not isinstance(data, dict):
        raise GeminiRequestError("Gemini returned an unexpected response format.")

    return {
        "budget": data.get("budget"),
        "people": data.get("people"),
        "categories": data.get("categories"),
        "priority": data.get("priority"),
    }
