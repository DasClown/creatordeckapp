import streamlit as st
import pandas as pd
import requests
import toml
import os
from datetime import datetime
from supabase import create_client
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Creator Deck", layout="wide", page_icon="⚫")

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #000000; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 3rem !important; font-weight: 900 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG LOADING (FAIL-SAFE) ---
def load_secrets():
    # 1. Versuch: Cloud Secrets (Flat Style - Bevorzugt)
    if "SUPABASE_URL" in st.secrets:
        return st.secrets
    
    # 2. Versuch: Cloud Secrets (Nested Style - Fallback für alte Configs)
    if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
        return {
            "SUPABASE_URL": st.secrets["supabase"]["url"],
            "SUPABASE_KEY": st.secrets["supabase"]["key"],
            "GEMINI_API_KEY": st.secrets.get("GEMINI_API_KEY"),
            "IG_USER_ID": st.secrets.get("IG_USER_ID"),
            "PAGE_ACCESS_TOKEN": st.secrets.get("PAGE_ACCESS_TOKEN"),
            "API_VERSION": st.secrets.get("API_VERSION", "v18.0")
        }

    # 3. Versuch: Lokale Datei secrets.toml
    if os.path.exists(".streamlit/secrets.toml"):
        return toml.load(".streamlit/secrets.toml")
    if os.path.exists("secrets.toml"):
        return toml.load("secrets.toml")
        
    st.error("❌ Keine Secrets gefunden! Bitte in Streamlit Cloud eintragen.")
    st.stop()

config = load_secrets()

# --- INIT CLIENTS ---
try:
    if "SUPABASE_URL" in config:
        supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_KEY"])
    else:
        st.error("Supabase URL fehlt in der Config.")
        st.stop()
        
    if "GEMINI_API_KEY" in config:
        genai.configure(api_key=config["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Setup Fehler: {e}")
    st.stop()

# --- MAIN APP LOGIC ---
st.title("ANTIGRAVITY DECK ⚡")

# Verbindungstest anzeigen
st.success("Verbindung hergestellt.")

# Daten Laden (Dummy für Test, wenn API fehlt)
st.write("System Status: Online")

# Snapshot Funktion (Test)
if st.button("Test Snapshot to Database"):
    try:
        data = {"date": datetime.now().strftime("%Y-%m-%d"), "followers": 0, "media_count": 0, "avg_engagement": 0}
        supabase.table("instagram_history").upsert(data, on_conflict="date").execute()
        st.toast("Datenbank Schreibzugriff erfolgreich!", icon="✅")
    except Exception as e:
        st.error(f"Datenbank Fehler: {e}")
