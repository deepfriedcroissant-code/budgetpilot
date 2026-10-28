"""Gemini shopping-intent parser. Network calls occur only on explicit invocation."""
import json
import os


def parse_request(message: str) -> dict:
    """Return {budget, people, categories, priority} from a user message.

    Budget and categories are required downstream; do not invent missing values.
    A person count is optional. Gemini never sets product IDs or prices.
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please enter a shopping request.")

    # Lazy imports let the backend and unit tests run without API credentials.
    from dotenv import load_dotenv
    from google import genai
    from catalog import CATEGORIES

    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing; configure your local .env.")

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
        "Do not create a cart. Shopping request: " + message
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    if not response.text:
        raise ValueError("Gemini returned no content.")
    data = json.loads(response.text)
    if not isinstance(data, dict):
        raise ValueError("Gemini must return a JSON object.")
    return {
        "budget": data.get("budget"),
        "people": data.get("people"),
        "categories": data.get("categories"),
        "priority": data.get("priority"),
    }
