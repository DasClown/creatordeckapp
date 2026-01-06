import streamlit as st
import requests
from supabase import create_client, Client

# 1. BOOT SEQUENCE
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# 2. UI ARCHITECTURE
st.set_page_config(page_title="CONTENT CORE", layout="wide")

# CSS Fix für Sidebar-Sichtbarkeit und Engine-Branding
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    [data-testid="stSidebar"] { background-color: #F8F8F8 !important; border-right: 1px solid #000; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    .stMetric { border: 1px solid #000; padding: 15px; border-radius: 0px; }
    </style>
""", unsafe_allow_html=True)

# 3. ENGINE LOGIC
def run_core_sync(url):
    headers = {
        "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
        "x-rapidapi-host": "instagram-statistics-api.p.rapidapi.com"
    }
    try:
        with st.spinner("CORE SYNC IN PROGRESS..."):
            res = requests.get("https://instagram-statistics-api.p.rapidapi.com/community", 
                               headers=headers, params={"url": url}, timeout=10)
            if res.status_code == 200:
                d = res.json().get("data", {})
                payload = {
                    "user_id": "janick@icanhasbucket.de",
                    "handle": d.get("screenName"),
                    "followers": d.get("usersCount"),
                    "engagement_rate": d.get("avgER"),
                    "quality_score": d.get("qualityScore")
                }
                supabase.table("stats_history").insert(payload).execute()
                st.rerun()
    except Exception as e:
        st.error(f"SYNC FAILED: {e}")

# 4. INTERFACE EXECUTION
st.title("CONTENT CORE / ENGINE")

# SIDEBAR - KEY FIXED
with st.sidebar:
    st.header("SYSTEM CONTROL")
    # Absolut statischer Key, um 'Multiple Elements' Error zu verhindern
    input_url = st.text_input("TARGET URL", key="engine_terminal_input_v3")
    if st.button("EXECUTE SYNC", key="engine_terminal_button_v3"):
        if input_url:
            run_core_sync(input_url)

# DATA DISPLAY
try:
    data = supabase.table("stats_history")\
        .select("*")\
        .eq("user_id", "janick@icanhasbucket.de")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    
    if data.data:
        s = data.data[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("FOLLOWERS", f"{int(s['followers']):,}")
        col2.metric("ENG_RATE", f"{float(s['engagement_rate']):.2%}")
        col3.metric("CORE SCORE", f"{float(s['quality_score']):.1f}")
    else:
        st.info("ENGINE READY. WAITING FOR INITIAL DATA SYNC.")
except Exception as e:
    st.error(f"DATABASE CONNECTION ERROR: {e}")
