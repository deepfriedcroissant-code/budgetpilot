"""Owner: Brigitte — shopping request input and parser integration."""
import streamlit as st
from parser import parse_request

EXAMPLE_REQUESTS = (
    "Snacks and drinks for 20 people under $100",
    "Snacks for 10 students under $50",
    "Drinks for 5 guests under $25",
)

def _use_example(text: str) -> None:
    """Callback: put an example into the text box."""
    st.session_state["shopping_request_text"] = text

def render_request_input() -> tuple[dict | None, str | None]:
    """Return (parsed request, error); (None, None) means no submission.

    TODO (Brigitte): improve examples/layout and connect the Gemini parser
    when parser.py is ready. Its current implementation is a mock.
    Coordinate validation and API error wording with Chenfei.
    """
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
        
    except Exception:
        # Keep provider responses and credentials out of the user interface.
        return None, "We could not process your request. Please try again."
