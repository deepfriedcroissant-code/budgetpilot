"""Frontend team: run with `streamlit run app.py`."""
import streamlit as st
from main import build_cart
from optimizer import calculate_total
from paypal_api import create_order

st.title('BudgetPilot')
st.caption('Hackathon demo: payments are simulated; no PayPal connection.')
message = st.text_area('What do you need?', 'Snacks and drinks for 10 people under $50')
if st.button('Generate recommendations'):
    st.session_state['result'] = build_cart(message)
if 'result' in st.session_state:
    request, cart, catalog = st.session_state['result']
    st.json(request)
    for item in cart:
        p = catalog[item['id']]
        st.write(f"{item['quantity']} × {p['name']} — ${p['price']}")
    st.metric('Cart total', f'${calculate_total(cart, catalog):.2f}')
    if st.checkbox('I approve this cart') and st.button('Simulate checkout'):
        st.success(f"Simulated checkout: {create_order(cart, catalog)['order_id']}")
