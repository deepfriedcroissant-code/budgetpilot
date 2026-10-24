"""Owner: Chenfei — request validation and friendly error messages."""
from decimal import Decimal, InvalidOperation
import streamlit as st


def render_request_feedback(request: dict | None, error: str | None = None) -> bool:
    """Display starter feedback; return True only when validation succeeds.

    TODO (Chenfei): connect validate_request() when validator.py exists,
    validate categories against the catalog, and distinguish API failures.
    The mock parser currently fills missing budgets/people with defaults;
    coordinate with Brigitte so missing input survives parsing for validation.
    """
    if error:
        st.error(error)
        return False
    if request is None:
        return False
    if not isinstance(request, dict):
        st.error("We could not understand that request. Please try again.")
        return False
    try:
        budget = Decimal(str(request.get("budget")))
        if not budget.is_finite() or budget <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        st.warning("Please provide a budget greater than zero.")
        return False
    if not request.get("categories"):
        st.warning("Please specify the product categories you need.")
        return False
    st.success("Request received. Ready to generate recommendations.")
    return True
