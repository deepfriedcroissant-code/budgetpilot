
import math

REQUIRED_FIELDS = {"budget", "people", "categories", "priority"}


def validate_request(data):
    """Return True for valid parser output; raise ValueError otherwise."""

    if not isinstance(data, dict):
        raise ValueError("Request data must be a dictionary.")

    fields = set(data.keys())
    missing = REQUIRED_FIELDS - fields
    extra = fields - REQUIRED_FIELDS

    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected fields: {sorted(extra)}")

    budget = data["budget"]
    people = data["people"]
    categories = data["categories"]
    priority = data["priority"]

    if isinstance(budget, bool) or not isinstance(budget, (int, float)):
        raise ValueError("Budget must be a number.")
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("Budget must be positive and finite.")

    if isinstance(people, bool) or not isinstance(people, int):
        raise ValueError("People must be an integer.")
    if people <= 0:
        raise ValueError("People must be a positive integer.")

    if not isinstance(categories, list) or not categories:
        raise ValueError("Categories must be a nonempty list.")
    if not all(
        isinstance(category, str) and category.strip()
        for category in categories
    ):
        raise ValueError("Each category must be a nonempty string.")

    # priority is optional: Gemini may return JSON null, which becomes None.
    if priority is not None and (
        not isinstance(priority, str) or not priority.strip()
    ):
        raise ValueError("Priority must be a nonempty string or None.")

    return True
