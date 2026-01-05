import streamlit as st
import pandas as pd
import requests
import toml
import os
from datetime import datetime
from supabase import create_client
import google.generativeai as genai
import plotly.express as px

# Module importieren
from modules import crm, finance, planner

# --- PAGE CONFIG ---
st.set_page_config(page_title="CreatorOS", layout="wide", page_icon="⚫")

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #000000; color: #ffffff; }
    header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #111; }
    [data-testid="stMetricValue"] { font-size: 3rem !important; font-weight: 900 !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG & LOGIN (GEKÜRZT) ---
def load_config():
    return st.secrets if "SUPABASE_URL" in st.secrets else toml.load(".streamlit/secrets.toml")

config = load_config()

def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("SYSTEM LOCKED 🔒")
    pwd = st.text_input("Access Code", type="password")
    if st.button("UNLOCK"):
        if pwd == config.get("APP_PASSWORD", "Start123!"):
            st.session_state.password_correct = True
            st.rerun()
    return False

if not check_password(): st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title("CreatorOS")
    page = st.radio("NAVIGATION", ["DASHBOARD", "CRM", "FINANCE", "PLANNER"])
    st.divider()
    if st.button("LOGOUT"):
        st.session_state.password_correct = False
        st.rerun()

# --- MODULE ROUTING ---
if page == "DASHBOARD":
    st.title("ANTIGRAVITY DECK 🚀")
    # Hier kommt Ihr bestehender Dashboard-Code (Tabs, Charts etc.) rein
    st.write("Dashboard Active")

elif page == "CRM":
    crm.render_crm()

elif page == "FINANCE":
    finance.render_finance()

elif page == "PLANNER":
    planner.render_planner()
