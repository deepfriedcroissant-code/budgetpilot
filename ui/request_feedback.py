"""Owner: Chenfei — request feedback integrated with backend validation.

Adapted from Chenfei's 'request_feedback_with_scenarios.py'. The original
standalone file stays on its feature branch; no example code executes on import.
"""
import streamlit as st
from validator import validate_request


def render_request_feedback(
    request: dict | None,
    error: str | None = None,
    *,
    input_text: str | None = None,
    supported_categories: list[str] | None = None,
) -> bool:
    """Show friendly errors, returning True only for a valid request."""
    if input_text is not None and not input_text.strip():
        st.warning("Please enter a shopping request first.")
        return False
    if error:
        st.error(error)
        return False
    if request is None:
        return False
    try:
        validate_request(request)
    except (ValueError, TypeError, KeyError) as exc:
        st.warning(str(exc))
        return False
    if supported_categories is not None:
        unknown = set(request["categories"]) - set(supported_categories)
        if unknown:
            st.warning("Unsupported categories: " + ", ".join(sorted(unknown)))
            return False
    st.success("Request validated. Recommendations are ready.")
    return True
