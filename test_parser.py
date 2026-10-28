import pytest
from validator import validate_request


def make_request(**overrides):
    data = {
        "budget": 100.0,
        "people": 20,
        "categories": ["snacks"],
        "priority": None,
    }
    data.update(overrides)
    return data


def test_valid_request():
    assert validate_request(make_request()) is True


def test_valid_request_with_priority():
    data = make_request(priority="variety")
    assert validate_request(data) is True


def test_accepts_various_valid_numbers():
    for budget, people in [(25, 3), (100.50, 20), (0.01, 1)]:
        assert validate_request(
            make_request(budget=budget, people=people)
        ) is True


def test_rejects_nonpositive_budget():
    with pytest.raises(ValueError):
        validate_request(make_request(budget=0))


def test_rejects_missing_field():
    data = make_request()
    del data["categories"]

    with pytest.raises(ValueError, match="Missing required fields"):
        validate_request(data)


def test_rejects_missing_budget_value():
    with pytest.raises(ValueError, match="Budget must be a number"):
        validate_request(make_request(budget=None))


def test_rejects_invalid_categories():
    with pytest.raises(ValueError, match="nonempty string"):
        validate_request(make_request(categories=["snacks", ""]))


def test_rejects_invalid_people_count():
    with pytest.raises(ValueError, match="positive integer"):
        validate_request(make_request(people=0))
