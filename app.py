import streamlit as st
import toml
import os

# Module importieren
from modules import crm, finance, planner, factory, gallery, channels, deals, demo
import pandas as pd
import google.generativeai as genai

# --- SETUP ---
st.set_page_config(page_title="CreatorOS", layout="wide", page_icon="⚫")

# --- CSS STYLING (WHITE & CLEAN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* Hintergrund und Grundschrift */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
        color: #1a1a1a;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eeeeee;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #ffffff;
        color: #1a1a1a;
        border: 1px solid #dddddd;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #000000;
        background-color: #f8f9fa;
    }

    /* Metriken */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: #000000 !important;
    }
    
    /* Akzentuierte Metriken */
    [data-testid="stMetricDelta"] > div {
        font-weight: 500 !important;
    }

    /* Erfolg/Einnahmen (Grün) */
    div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaDirection-Up"] {
        color: #28a745 !important;
    }

    /* Verlust/Ausgaben (Rot) */
    div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaDirection-Down"] {
        color: #dc3545 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #888888;
    }
    .stTabs [aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 2px solid #000000 !important;
    }

    /* Input Felder */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border: 1px solid #eeeeee;
        border-radius: 8px;
    }
    
    /* Karten-Effekt für Boxen */
    .ai-box, .custom-card {
        background-color: #fdfdfd;
        border: 1px solid #eeeeee;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

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
    
    # Metriken
    c1, c2, c3 = st.columns(3)
    c1.metric("Reach", "125.400", "+8.2%")
    c2.metric("Engagement", "12.300", "-1.5%")
    c3.metric("Followers", "45.120", "+0.4%")
    
    st.info("💡 Dashboard-Logik wird hier integriert (Instagram API, Analytics, etc.)")

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
