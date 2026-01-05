import streamlit as st
import toml
import os

# Module importieren
from modules import crm, finance, planner, factory, gallery, channels, deals, demo
import pandas as pd
import google.generativeai as genai
from supabase import create_client

# --- SETUP ---
st.set_page_config(page_title="CreatorOS", layout="wide", page_icon="⚫")

# --- ANALYTICS ---
st.markdown("""
    <script src="https://cdn.usefathom.com/script.js" data-site="YOUR_ID" defer></script>
""", unsafe_allow_html=True)

# --- CSS STYLING (RADICAL MINIMALISM) ---
st.markdown("""
<style>
    /* Google Font: Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Radikaler Minimalismus: Keine Schatten, nur 1px Linien */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E0E0E0 !important;
    }

    /* Card-Ersatz: Flache Boxen */
    .stMetric, .ai-box, .custom-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 0px !important; /* Harte Kanten für edlen Look */
        padding: 20px !important;
        box-shadow: none !important;
    }

    /* Buttons: Black & White */
    .stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 0px !important;
        border: 1px solid #000000 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 0px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: #FFFFFF !important;
    }

    /* Metriken */
    [data-testid="stMetricValue"] {
        font-weight: 300 !important;
        letter-spacing: -1px;
        font-size: 2.5rem !important;
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
</style>
""", unsafe_allow_html=True)

# --- LANDING PAGE ---
def render_landing_page():
    # Hero Section
    st.markdown("""
        <div style='padding: 100px 20px; text-align: center;'>
            <h1 style='font-size: 72px; font-weight: 300; letter-spacing: -2px; margin-bottom: 10px;'>
                CREATOR OS
            </h1>
            <p style='font-size: 20px; color: #666; font-weight: 300; margin-bottom: 40px;'>
                The Intelligence Layer for High-Scale Creators.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Value Propositions (3 Spalten)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 01 ANALYZE")
        st.caption("Echtzeit-Performance-Tracking über alle Plattformen hinweg. Automatisierte Daten-Snapshots jede Nacht.")

    with col2:
        st.markdown("### 02 GENERATE")
        st.caption("AI-Factory, die deinen Erfolg versteht. Captions und Hooks basierend auf deinen Top-Inhalten.")

    with col3:
        st.markdown("### 03 SCALE")
        st.caption("Deals, Cashflow und Redaktionsplan in einer einzigen, sauberen Oberfläche.")

    st.divider()

    # Login / Access Trigger
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
        if st.button("ENTER TERMINAL"):
            st.session_state.view = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- VIEW MANAGEMENT ---
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

# Landing Page
if st.session_state.view == "landing":
    render_landing_page()
    st.stop()

# Login Check
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

# --- SUPABASE INIT ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

# --- ROUTING ---
if page == "DASHBOARD":
    st.title("ANTIGRAVITY DECK 🚀")
    
    # Metriken
    c1, c2, c3 = st.columns(3)
    c1.metric("Reach", "125.400", "+8.2%")
    c2.metric("Engagement", "12.300", "-1.5%")
    c3.metric("Followers", "45.120", "+0.4%")
    
    # Critical Alerts System
    supabase = init_supabase()
    if supabase:
        from datetime import datetime, timedelta
        
        st.divider()
        st.subheader("⚠️ CRITICAL ALERTS")
        
        try:
            # 1. Deals laden, die bald fällig sind
            threshold = datetime.now() + timedelta(hours=48)
            res_deals = supabase.table("deals").select("*").lte("deadline", str(threshold.date())).eq("status", "Closed").execute()
            
            # 2. Content Plan laden, um Assets zu prüfen
            res_plan = supabase.table("content_plan").select("title, platform").execute()
            planned_titles = [item['title'] for item in res_plan.data] if res_plan.data else []

            alerts_found = False
            for deal in res_deals.data if res_deals.data else []:
                # Prüfung: Gibt es einen entsprechenden Eintrag im Content Plan?
                if deal['brand'] not in str(planned_titles):
                    st.error(f"**MISSING ASSET:** Für den Deal mit '{deal['brand']}' (Fällig: {deal['deadline']}) wurde noch kein Content geplant!")
                    alerts_found = True
                    
            if not alerts_found:
                st.success("✅ Alle fälligen Deals sind im Zeitplan. Keine kritischen Warnungen.")
        except Exception as e:
            st.warning(f"Alerts konnten nicht geladen werden: {e}")
    
    st.info("💡 Dashboard-Logik wird hier integriert (Instagram API, Analytics, etc.)")

elif page == "GALLERY":
    supabase = init_supabase()
    if supabase:
        gallery.render_gallery(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Gallery benötigt Cloud Storage.")

elif page == "CHANNELS":
    channels.render_channels()

elif page == "DEALS":
    deals.render_deals()

elif page == "CRM":
    supabase = init_supabase()
    if supabase:
        crm.render_crm(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Bitte SUPABASE_URL und SUPABASE_KEY in secrets.toml hinzufügen.")

elif page == "FINANCE":
    supabase = init_supabase()
    if supabase:
        finance.render_finance(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Bitte SUPABASE_URL und SUPABASE_KEY in secrets.toml hinzufügen.")

elif page == "PLANNER":
    supabase = init_supabase()
    if supabase:
        planner.render_planner(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Bitte SUPABASE_URL und SUPABASE_KEY in secrets.toml hinzufügen.")

elif page == "DEMO":
    demo.render_demo()

elif page == "FACTORY":
    # Gemini API konfigurieren
    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
    
    # Supabase für Performance-Daten
    supabase = init_supabase()
    if supabase:
        factory.render_factory(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Factory benötigt Zugriff auf Performance-Daten.")
