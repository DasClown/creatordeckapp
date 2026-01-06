import streamlit as st
import requests
from supabase import create_client, Client

# 1. SYSTEM INITIALISIERUNG (Single-Check)
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# 2. UI STYLING & SIDEBAR VISIBILITY
st.set_page_config(page_title="CONTENT CORE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    [data-testid="stSidebar"] { background-color: #F8F8F8 !important; border-right: 1px solid #000; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    .stMetric { border: 1px solid #000; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. CORE LOGIK: SYNC
def execute_sync(profile_url, supabase):
    api_url = "https://instagram-statistics-api.p.rapidapi.com/community"
    headers = {
        "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
        "x-rapidapi-host": "instagram-statistics-api.p.rapidapi.com"
    }
    try:
        with st.spinner("SYNCING..."):
            res = requests.get(api_url, headers=headers, params={"url": profile_url}, timeout=10)
            if res.status_code == 200:
                d = res.json().get("data", {})
                payload = {
                    "user_id": st.session_state.user_email,
                    "handle": d.get("screenName"),
                    "followers": d.get("usersCount"),
                    "engagement_rate": d.get("avgER"),
                    "quality_score": d.get("qualityScore")
                }
                supabase.table("stats_history").insert(payload).execute()
                st.rerun()
    except Exception as e:
        st.error(f"SYNC ERROR: {e}")

# 4. ENGINE INTERFACE
def main():
    # Session State Setup
    if "user_email" not in st.session_state:
        st.session_state.user_email = "janick@icanhasbucket.de"
    
    supabase = get_supabase()

    st.title("CONTENT CORE / ENGINE")

    # SIDEBAR (Hier lag der Fehler)
    # Wir nutzen einen statischen Key ohne Variablen-Interpolation
    with st.sidebar:
        st.markdown("### 🌀 SYSTEM CONTROL")
        target_url = st.text_input("IG URL", key="final_engine_input_fixed")
        if st.button("INITIALIZE SYNC", key="final_engine_button_fixed"):
            if target_url:
                execute_sync(target_url, supabase)

    # DISPLAY AREA
    try:
        res = supabase.table("stats_history")\
            .select("*")\
            .eq("user_id", st.session_state.user_email)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if res.data:
            s = res.data[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("FOLLOWERS", f"{int(s['followers']):,}")
            col2.metric("ENG_RATE", f"{float(s['engagement_rate']):.2%}")
            col3.metric("CORE SCORE", f"{float(s['quality_score']):.1f}")
        else:
            st.info("NO DATA LOADED. USE SIDEBAR.")
            
    except Exception as e:
        st.error(f"DATABASE ERROR: {e}")

if __name__ == "__main__":
    main()
