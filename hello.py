import streamlit as st
import requests
from supabase import create_client, Client
import pandas as pd

# 1. INITIALISIERUNG
try:
    # Direkter Stopp bei fehlenden Secrets
    for secret in ["SUPABASE_URL", "SUPABASE_KEY", "RAPIDAPI_KEY"]:
        if secret not in st.secrets:
            st.error(f"CRITICAL: {secret} missing")
            st.stop()
            
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"BOOT ERROR: {e}")
    st.stop()

# 2. THEME & UI FIX
st.set_page_config(page_title="CONTENT CORE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    /* Sidebar Text-Sichtbarkeit erzwingen */
    [data-testid="stSidebar"] { background-color: #F8F8F8 !important; border-right: 1px solid #000; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    /* Metriken Styling */
    [data-testid="stMetric"] { border: 1px solid #000; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

# 3. CORE LOGIK: SYNC
def run_sync(profile_url):
    api_url = "https://instagram-statistics-api.p.rapidapi.com/community"
    headers = {
        "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
        "x-rapidapi-host": "instagram-statistics-api.p.rapidapi.com"
    }
    try:
        with st.spinner("SYNCING CORE..."):
            res = requests.get(api_url, headers=headers, params={"url": profile_url}, timeout=10)
            if res.status_code == 200:
                d = res.json().get("data", {})
                payload = {
                    "user_id": st.session_state.get("user_email", "janick@icanhasbucket.de"),
                    "handle": d.get("screenName"),
                    "followers": d.get("usersCount"),
                    "engagement_rate": d.get("avgER"),
                    "quality_score": d.get("qualityScore")
                }
                supabase.table("stats_history").insert(payload).execute()
                st.success("SYNC OK")
                st.rerun()
    except Exception as e:
        st.error(f"SYNC ERROR: {e}")

# 4. ENGINE INTERFACE
def main():
    if "user_email" not in st.session_state:
        st.session_state.user_email = "janick@icanhasbucket.de"

    st.title("CONTENT CORE / ENGINE")

    # SIDEBAR
    with st.sidebar:
        st.markdown("### 🌀 SYSTEM CONTROL")
        # KEY-FIX: Eindeutiger Key verhindert Duplicate Element Error
        input_url = st.text_input("IG URL", key="engine_unique_v2_input")
        if st.button("INITIALIZE SYNC", key="engine_unique_v2_btn"):
            if input_url:
                run_sync(input_url)

    # DISPLAY
    try:
        res = supabase.table("stats_history")\
            .select("*")\
            .eq("user_id", st.session_state.user_email)\
            .order("created_at", desc=True)\
            .execute()
        
        if res.data:
            latest = res.data[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("FOLLOWERS", f"{int(latest['followers']):,}")
            c2.metric("ENG_RATE", f"{float(latest['engagement_rate']):.2%}")
            c3.metric("CORE SCORE", f"{float(latest['quality_score']):.1f}")
        else:
            st.info("NO DATA LOADED.")
            
    except Exception as e:
        st.error(f"ENGINE ERROR: {e}")

if __name__ == "__main__":
    main()
