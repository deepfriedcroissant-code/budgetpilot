import math

# required fields I can think of
REQUIRED_FIELDS = {"budget", "people", "categories"}


def validate_request(data):
    """
    Validate structured shopping-request data.

    Returns:
        True if the data is valid.

    Raises:
        ValueError: If the data is missing fields, has extra fields,
                    or contains invalid values.
    """
    if not isinstance(data, dict):
        raise ValueError("Request data must be a dictionary.")

    fields = set(data.keys())

    missing = REQUIRED_FIELDS - fields
    extra = fields - REQUIRED_FIELDS

    # cover lots of potential cases

    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    if extra:
        raise ValueError(f"Unexpected fields: {sorted(extra)}")

    budget = data["budget"]
    people = data["people"]
    categories = data["categories"]

    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(budget, bool) or not isinstance(budget, (int, float)):
        raise ValueError("Budget must be a number.")

    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("Budget must be positive and finite.")

    if isinstance(people, bool) or not isinstance(people, int):
        raise ValueError("People must be an integer.")

    if people <= 0:
        raise ValueError("People must be a positive integer.")

    if not isinstance(categories, list):
        raise ValueError("Categories must be a list.")

    if not categories:
        raise ValueError("Categories must contain at least one item.")

    if not all(
        isinstance(category, str) and category.strip()
        for category in categories
    ):
        raise ValueError(
            "Each category must be a nonempty string."
        )

    return True
