import streamlit as st
import toml
import os

# Module importieren
from modules import crm, finance, planner

# --- SETUP ---
st.set_page_config(page_title="CreatorOS", layout="wide", page_icon="⚫")

# CSS (identisch zu vorher)
st.markdown("<style>html, body, [class*='css'] { font-family: 'Inter', sans-serif; background-color: #000000; color: #ffffff; } header {visibility: hidden;} [data-testid='stSidebar'] { background-color: #050505; border-right: 1px solid #111; }</style>", unsafe_allow_html=True)

# Login Check (Gekürzt für Übersicht)
if "password_correct" not in st.session_state: st.session_state.password_correct = False
if not st.session_state.password_correct:
    pwd = st.text_input("Access Code", type="password")
    if st.button("UNLOCK"):
        if pwd == st.secrets.get("APP_PASSWORD", "Start123!"):
            st.session_state.password_correct = True
            st.rerun()
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title("CreatorOS")
    page = st.radio("NAVIGATION", ["DASHBOARD", "CRM", "FINANCE", "PLANNER"])
    st.divider()
    if st.button("LOGOUT"):
        st.session_state.password_correct = False
        st.rerun()

# --- ROUTING ---
if page == "DASHBOARD":
    st.title("ANTIGRAVITY DECK 🚀")
    st.write("Dashboard Logik hier...") # Hier den alten Dashboard Code einfügen

elif page == "CRM":
    crm.render_crm()

elif page == "FINANCE":
    finance.render_finance()

elif page == "PLANNER":
    planner.render_planner()
