"""Owner: Brigitte — shopping request input and Gemini parser connection."""
import streamlit as st
from parser import (
    GeminiConfigurationError,
    GeminiRequestError,
    parse_request,
)

EXAMPLE_REQUESTS = (
    "Snacks and drinks for 20 people under $100",
    "Snacks for 10 students under $50",
    "Drinks for 5 guests under $25",
)


def _use_example(text: str) -> None:
    st.session_state["shopping_request_text"] = text


def render_request_input() -> tuple[dict | None, str | None]:
    """Return (parsed_request, error); (None, None) means no submission."""
    st.subheader("Describe your shopping request")
    with st.expander("Example requests"):
        st.caption("Click an example to fill in the text box.")
        for i, example in enumerate(EXAMPLE_REQUESTS):
            st.button(
                example,
                key=f"example_request_{i}",
                on_click=_use_example,
                args=(example,),
                use_container_width=True,
            )

    with st.form("shopping_request_form"):
        message = st.text_area(
            "What do you need?",
            key="shopping_request_text",
            placeholder="e.g. Snacks and drinks for 20 people under $100",
        )
        submitted = st.form_submit_button("Generate Cart", type="primary")

    if not submitted:
        return None, None
    if not message.strip():
        return None, "Please enter a shopping request."

    try:
        with st.spinner("Interpreting your request…"):
            return parse_request(message.strip()), None
    except (GeminiConfigurationError, GeminiRequestError, ValueError) as exc:
        # These exceptions contain curated, safe user-facing messages.
        return None, str(exc)
    except Exception:
        # Avoid exposing credentials or provider debug traces to the UI.
        return None, (
            "Gemini encountered an unexpected error. "
            "Check the VS Code terminal for a traceback and verify your local .env."
        )
