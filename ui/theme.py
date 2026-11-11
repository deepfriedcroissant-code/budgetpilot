"""Minimal visual system for the public-facing BudgetPilot shopping demo."""
import streamlit as st

STYLES = """
<style>
/* Keep visual polish lightweight and Streamlit-native. */
.stApp {background: radial-gradient(circle at 90% 0%, #e9f2ff 0, transparent 30%), #f8fafc;}
section[data-testid="stSidebar"] {background: #f0f5ff;}
.block-container {padding-top: 1.7rem; max-width: 1220px;}
div[data-testid="stMetric"] {
  background: white; border: 1px solid #e2e8f0;
  padding: 0.9rem 1rem; border-radius: 15px;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  transition: transform .22s ease, box-shadow .22s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  transform: translateY(-3px); box-shadow: 0 9px 30px rgba(22,46,79,.08);
}
.bp-hero {
  padding: 1.5rem 1.6rem; border-radius: 22px;
  background: linear-gradient(115deg,#102650,#1a4383 70%,#2575c7);
  color: white; margin-bottom: 1.3rem;
}
.bp-hero h1 {color: white; margin: 0 0 .35rem 0; font-size: 2.35rem; letter-spacing: -.04em;}
.bp-hero p {margin: 0; color: #e2ebff; font-size: 1.05rem;}
.bp-step {font-weight: 700; font-size: .9rem; color: #2563eb; letter-spacing: .07em;}
.bp-thumb {
  border-radius: 15px; background: linear-gradient(135deg,#edf4ff,#e2edf9);
  display:flex; align-items:center; justify-content:center; height:115px;
  font-size: 3.5rem; margin-bottom:.65rem;
}
.bp-product-name {font-weight: 700; font-size: 1.04rem; min-height: 2.4rem;}
.bp-muted {font-size:.84rem; color: #64748b;}
.bp-price {font-size:1.45rem; font-weight:750; color:#0f326d; padding:.45rem 0;}
@keyframes bp-pop {0%{transform:scale(.97);opacity:.45} 100%{transform:scale(1);opacity:1}}
.bp-pop {animation:bp-pop .3s ease-out;}
@media(prefers-reduced-motion:reduce){
 .bp-pop {animation:none}
 div[data-testid="stVerticalBlockBorderWrapper"] {transition:none}
 div[data-testid="stVerticalBlockBorderWrapper"]:hover {transform:none}
}
</style>
"""

CATEGORY_ICONS = {
    "snacks": "🍿", "drinks": "🥤", "groceries": "🛒",
    "party_supplies": "🎉", "household": "🧼",
    "health": "🩹", "frozen": "🧊",
}
PRODUCT_ICONS = {
    "salted_chips": "🥔", "bbq_chips": "🥔", "tortilla_chips": "🌮",
    "popcorn": "🍿", "cookies": "🍪", "pretzels": "🥨",
    "trail_mix": "🥜", "granola_bars": "🍫", "gummy_bears": "🍬",
    "water": "💧", "sparkling_water": "🫧", "cola": "🥤",
    "orange_juice": "🍊", "juice_boxes": "🧃", "iced_tea": "🧋",
    "cold_brew": "☕", "bread": "🍞", "peanut_butter": "🥜",
    "jam": "🍓", "pasta": "🍝", "rice": "🍚", "eggs": "🥚",
    "milk": "🥛", "cheddar_cheese": "🧀", "bananas": "🍌",
    "paper_plates": "🍽️", "plastic_cups": "🥛",
}


def product_icon(item):
    return PRODUCT_ICONS.get(str(item.get("id")), CATEGORY_ICONS.get(item.get("category"), "🛍️"))


def apply_theme():
    st.markdown(STYLES, unsafe_allow_html=True)
