"""Gemini shopping-intent parser with explicit local .env support."""
import json
import os
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

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
    except Exception as exc:
        # Never surface provider exception strings or request headers:
        # some SDK exceptions can include sensitive request details.
        message_lower = str(exc).lower()
        if any(s in message_lower for s in ("api key not valid", "api_key_invalid", "invalid api key", "401", "unauthenticated")):
            explanation = "Gemini rejected the API key. Generate a new Gemini key and update your local .env."
        elif any(s in message_lower for s in ("quota", "rate limit", "429", "resource_exhausted")):
            explanation = "Gemini quota or rate limit reached. Check your Gemini API quota and retry later."
        elif any(s in message_lower for s in ("not found", "404", "model")):
            explanation = "The configured Gemini model may be unavailable. Check GEMINI_MODEL in your local .env."
        else:
            explanation = "Gemini could not be reached. Check your connection, key permissions, and model configuration."
        raise GeminiRequestError(explanation) from exc

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
