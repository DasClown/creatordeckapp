import streamlit as st
import pandas as pd
import requests
import toml
import os
import plotly.express as px
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
    header {visibility: hidden;}
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #000000; border: none; }
    [data-testid="stMetricValue"] { font-size: 3rem !important; font-weight: 900 !important; color: white !important; }
    .stTextInput > div > div > input { color: white; background-color: #111; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG LOADER ---
def load_config():
    if "SUPABASE_URL" in st.secrets: return st.secrets
    if "supabase" in st.secrets:
        return {
            "SUPABASE_URL": st.secrets["supabase"]["url"],
            "SUPABASE_KEY": st.secrets["supabase"]["key"],
            "GEMINI_API_KEY": st.secrets.get("GEMINI_API_KEY"),
            "IG_USER_ID": st.secrets.get("IG_USER_ID"),
            "PAGE_ACCESS_TOKEN": st.secrets.get("PAGE_ACCESS_TOKEN"),
            "APP_PASSWORD": st.secrets.get("APP_PASSWORD"),
            "API_VERSION": st.secrets.get("API_VERSION", "v19.0")
        }
    st.error("❌ Secrets fehlen."); st.stop()

config = load_config()

# --- GATEKEEPER (LOGIN) ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Login Maske
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("SYSTEM LOCKED 🔒")
        pwd = st.text_input("Access Code", type="password")
        if st.button("UNLOCK"):
            if pwd == config.get("APP_PASSWORD", "Start123!"):
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Access Denied.")
    return False

if not check_password():
    st.stop()

# --- INIT CLIENTS ---
try:
    supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_KEY"])
    genai.configure(api_key=config["GEMINI_API_KEY"])
except: st.error("Client Init Error"); st.stop()

# API Params
BASE_URL = f"https://graph.facebook.com/{config.get('API_VERSION', 'v19.0')}/"
PARAMS = {'access_token': config['PAGE_ACCESS_TOKEN']}

# --- DATA FUNCTIONS ---
@st.cache_data(ttl=600)
def fetch_live_data():
    try:
        profile = requests.get(BASE_URL + config['IG_USER_ID'], params={**PARAMS, 'fields': 'username,name,followers_count,media_count,profile_picture_url'}).json()
        if 'error' in profile: return profile, []
        media_resp = requests.get(BASE_URL + config['IG_USER_ID'] + "/media", params={**PARAMS, 'fields': 'id,caption,media_type,timestamp,like_count,comments_count,permalink,media_url,thumbnail_url', 'limit': 20}).json()
        posts = []
        if 'data' in media_resp:
            for p in media_resp['data']:
                try:
                    ins = requests.get(BASE_URL + p['id'] + "/insights", params={**PARAMS, 'metric': 'reach,impressions'}).json()
                    reach = ins['data'][0]['values'][0]['value'] if 'data' in ins else 0
                    imps = ins['data'][1]['values'][0]['value'] if 'data' in ins and len(ins['data']) > 1 else 0
                except: reach, imps = 0, 0
                img = p.get('thumbnail_url', p.get('media_url', ''))
                posts.append({'ID': p['id'], 'Datum': pd.to_datetime(p['timestamp']), 'Typ': p['media_type'], 'Caption': p.get('caption', '')[:50], 'Likes': p.get('like_count', 0), 'Reichweite': reach, 'Impressions': imps, 'Engagement': p.get('like_count', 0) + p.get('comments_count', 0), 'Image_URL': img, 'Link': p.get('permalink')})
        return profile, posts
    except: return {}, []

def save_snapshot(fol, med, eng):
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"date": today, "followers": fol, "media_count": med, "avg_engagement": eng}
    try: supabase.table("instagram_history").upsert(data, on_conflict="date").execute(); st.toast("Snapshot saved.", icon="⚫")
    except Exception as e: st.error(f"DB Error: {e}")

def load_history():
    try: res = supabase.table("instagram_history").select("*").order("date").execute(); return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except: return pd.DataFrame()

def run_ai(df_in):
    model = genai.GenerativeModel('gemini-1.5-flash')
    csv_txt = df_in[['Datum', 'Typ', 'Reichweite', 'Engagement']].to_csv(index=False)
    prompt = f"Analyze IG data:\n{csv_txt}\n1. Best content.\n2. Weakness.\n3. Action step. Short bullets."
    return model.generate_content(prompt).text

# --- DASHBOARD ---
prof, posts = fetch_live_data()
if not prof or 'error' in prof: st.error(prof.get('error', {}).get('message', 'API Error')); st.stop()
df = pd.DataFrame(posts)
fol = prof.get('followers_count', 0)
if not df.empty: df['ER'] = round((df['Engagement'] / fol) * 100, 2)

with st.sidebar:
    st.markdown("### ACCOUNT")
    st.caption(f"@{prof.get('username')}")
    st.metric("Follower", fol)
    st.divider()
    if st.button("SNAPSHOT"):
        avg = int(df['Engagement'].mean()) if not df.empty else 0
        save_snapshot(fol, prof.get('media_count'), avg)
    if st.button("LOGOUT"):
        st.session_state.password_correct = False
        st.rerun()

st.title("ANTIGRAVITY DECK 🚀")
t1, t2, t3 = st.tabs(["VISUALS", "DATA + AI", "TIMELINE"])
with t1:
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("REACH", int(df['Reichweite'].mean())); c2.metric("LIKES", int(df['Likes'].mean())); c3.metric("ER", f"{round(df['ER'].mean(), 2)}%"); c4.metric("PEAK", int(df['Reichweite'].max()))
        cols = st.columns(3)
        for i, row in df.iterrows():
            with cols[i % 3]:
                if row['Image_URL']: st.image(row['Image_URL'], use_container_width=True)
                st.caption(f"👁️ {row['Reichweite']} | ❤️ {row['Likes']}")
with t2:
    if not df.empty:
        c_ai, c_chart = st.columns([1, 2])
        with c_ai:
            if st.button("ANALYZE ⚡"):
                with st.spinner("Processing..."): st.markdown(f"<div class='ai-box'>{run_ai(df)}</div>", unsafe_allow_html=True)
        with c_chart: st.plotly_chart(px.line(df, x='Datum', y=['Reichweite', 'Impressions'], template="plotly_dark").update_layout(paper_bgcolor="black", plot_bgcolor="black"), use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
with t3:
    hist = load_history()
    if not hist.empty: 
        hist['date'] = pd.to_datetime(hist['date'])
        st.plotly_chart(px.area(hist, x='date', y='followers', template="plotly_dark").update_layout(paper_bgcolor="black", plot_bgcolor="black").update_traces(line_color="white", fillcolor="rgba(255,255,255,0.1)"), use_container_width=True)
