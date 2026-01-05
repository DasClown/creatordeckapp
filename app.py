import streamlit as st
import toml
import os

# Module importieren
from modules import crm, finance, planner, factory, gallery, channels, deals, demo
import pandas as pd
import google.generativeai as genai

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
    page = st.radio("NAVIGATION", [
        "DASHBOARD", "CHANNELS", "FACTORY", "GALLERY", "CRM", "DEALS", "FINANCE", "PLANNER", "DEMO"
    ])
    
    with st.expander("⚙️ SETTINGS"):
        st.caption("Connected: @user")
        if st.button("Sync APIs"):
            st.rerun()
        st.color_picker("Brand Color", "#ffffff")
    
    st.divider()
    if st.button("LOGOUT"):
        st.session_state.password_correct = False
        st.rerun()

# --- DEMO DATA (für Factory) ---
def get_demo_data():
    return pd.DataFrame({
        'Caption': ['Top Post 1', 'Top Post 2', 'Top Post 3'],
        'Engagement': [450, 380, 320]
    })

# --- ROUTING ---
if page == "DASHBOARD":
    st.title("ANTIGRAVITY DECK 🚀")
    st.write("Dashboard Logik hier...") # Hier den alten Dashboard Code einfügen

elif page == "GALLERY":
    gallery.render_gallery()

elif page == "CHANNELS":
    channels.render_channels()

elif page == "DEALS":
    deals.render_deals()

elif page == "CRM":
    crm.render_crm()

elif page == "FINANCE":
    finance.render_finance()

elif page == "PLANNER":
    planner.render_planner()

elif page == "DEMO":
    demo.render_demo()

elif page == "FACTORY":
    # Gemini API konfigurieren
    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
    
    # Prüfen ob Post-Daten im Session State vorhanden sind
    if 'df_posts' in st.session_state and not st.session_state.df_posts.empty:
        factory.render_factory(st.session_state.df_posts)
    else:
        # Fallback auf Demo-Daten
        st.info("💡 Tipp: Lade zuerst das Dashboard, um echte Instagram-Daten zu verwenden.")
        df_history = get_demo_data()
        factory.render_factory(df_history)
