import streamlit as st
import pandas as pd
import requests
import toml
import plotly.express as px
import os
from datetime import datetime
from supabase import create_client, Client
import google.generativeai as genai

# --- SETUP & STYLE ---
st.set_page_config(page_title="Creator Deck", layout="wide", page_icon="⚫")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #000000; color: #ffffff; }
    header {visibility: hidden;}
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #000000; border: none; }
    [data-testid="stMetricValue"] { font-size: 3rem !important; font-weight: 900 !important; color: white !important; }
    .stButton > button { border: 1px solid #333; border-radius: 30px; color: white; background: transparent; }
    .stButton > button:hover { border-color: white; background: white; color: black; }
    .ai-box { border-left: 2px solid white; padding-left: 20px; margin-top: 20px; color: #ccc; }
</style>
""", unsafe_allow_html=True)

# --- ROBUST CONFIG LOADER (Das Herzstück) ---
def find_secret(key_name):
    """Sucht einen Key überall in st.secrets, egal ob flach oder verschachtelt."""
    # 1. Suche direkt (Flat)
    if key_name in st.secrets:
        return st.secrets[key_name]
    
    # 2. Suche in Untergruppen (z.B. [supabase])
    for section in st.secrets:
        if isinstance(st.secrets[section], dict):
            if key_name in st.secrets[section]:
                return st.secrets[section][key_name]
                
    return None

def get_config():
    # Liste der benötigten Keys
    required_keys = ["SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY", "PAGE_ACCESS_TOKEN", "IG_USER_ID", "API_VERSION"]
    loaded_config = {}
    missing_keys = []

    # Versuch 1: Aus Cloud Secrets laden (intelligent)
    for key in required_keys:
        val = find_secret(key)
        if val:
            loaded_config[key] = val
        else:
            missing_keys.append(key)

    # Versuch 2: Falls Cloud leer, versuche lokale Datei (Fallback)
    if missing_keys and os.path.exists("secrets.toml"):
        try:
            local_toml = toml.load("secrets.toml")
            for key in missing_keys:
                if key in local_toml:
                    loaded_config[key] = local_toml[key]
                    # Entferne aus missing list, da gefunden
        except:
            pass

    # Ergebnis prüfen
    # Wir prüfen hier nur SUPABASE und TOKEN kritisch
    if "SUPABASE_URL" not in loaded_config or "PAGE_ACCESS_TOKEN" not in loaded_config:
        st.error(f"❌ KONFIGURATIONS-FEHLER: Folgende Secrets fehlen: {missing_keys}")
        st.info(f"Gefundene Keys in st.secrets: {list(st.secrets.keys())}")
        st.stop()
        
    return loaded_config

config = get_config()

# --- INIT CLIENTS ---
try:
    supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_KEY"])
    genai.configure(api_key=config["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"❌ Client Init Fehler: {e}")
    st.stop()

# API Params
BASE_URL = f"https://graph.facebook.com/{config['API_VERSION']}/"
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
                posts.append({
                    'ID': p['id'], 'Datum': pd.to_datetime(p['timestamp']), 'Typ': p['media_type'],
                    'Caption': p.get('caption', '')[:50], 'Likes': p.get('like_count', 0),
                    'Kommentare': p.get('comments_count', 0), 'Reichweite': reach, 'Impressions': imps,
                    'Engagement': p.get('like_count', 0) + p.get('comments_count', 0),
                    'Image_URL': img, 'Link': p.get('permalink')
                })
        return profile, posts
    except Exception as e:
        st.error(f"API Fetch Fehler: {e}")
        return {}, []

def save_snapshot_supabase(fol, med, eng):
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"date": today, "followers": fol, "media_count": med, "avg_engagement": eng}
    try:
        supabase.table("instagram_history").upsert(data, on_conflict="date").execute()
        st.toast("Snapshot gespeichert!", icon="⚫")
    except Exception as e:
        st.error(f"Supabase Write Fehler: {e}")

def load_history_supabase():
    try:
        response = supabase.table("instagram_history").select("*").order("date").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        # Silent fail für saubere UI beim ersten Start
        print(e)
        return pd.DataFrame()

def run_ai_analysis(df_input):
    model = genai.GenerativeModel('gemini-1.5-flash')
    csv_data = df_input[['Datum', 'Typ', 'Reichweite', 'Engagement', 'Caption']].to_csv(index=False)
    prompt = f"Act as a social media strategist. Analyze:\n{csv_data}\n1. Top content type/time.\n2. One weakness.\n3. One strict action step. Bullet points."
    return model.generate_content(prompt).text

# --- DASHBOARD RENDER ---
prof, posts = fetch_live_data()
if not prof or 'error' in prof: 
    if prof: st.error(prof['error']['message'])
    st.stop()

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
        save_snapshot_supabase(fol, prof.get('media_count'), avg)

st.title("ANTIGRAVITY DECK")
st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True) 

t1, t2, t3 = st.tabs(["VISUALS", "DATA + AI", "TIMELINE"])

with t1:
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("REACH", int(df['Reichweite'].mean()))
        c2.metric("LIKES", int(df['Likes'].mean()))
        c3.metric("ER", f"{round(df['ER'].mean(), 2)}%")
        c4.metric("PEAK", int(df['Reichweite'].max()))
        st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
        cols_per_row = 3
        for i in range(0, len(df), cols_per_row):
            cols = st.columns(cols_per_row)
            for col, (_, row) in zip(cols, df.iloc[i:i+cols_per_row].iterrows()):
                with col:
                    if row['Image_URL']: st.image(row['Image_URL'], use_container_width=True)
                    st.caption(f"👁️ {row['Reichweite']} | ❤️ {row['Likes']}")
    else:
        st.info("No posts yet. Post on Instagram to see data here.")
                    
with t2:
    if not df.empty:
        c_ai, c_chart = st.columns([1, 2])
        with c_ai:
            if st.button("ANALYZE ⚡"):
                with st.spinner("Thinking..."):
                    st.markdown(f"<div class='ai-box'>{run_ai_analysis(df)}</div>", unsafe_allow_html=True)
        with c_chart:
            fig = px.line(df, x='Datum', y=['Reichweite', 'Impressions'], template="plotly_dark")
            fig.update_layout(paper_bgcolor="black", plot_bgcolor="black", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['Datum', 'Typ', 'Reichweite', 'Likes', 'ER']].sort_values(by='Datum', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No data for analysis.")

with t3:
    hist = load_history_supabase()
    if not hist.empty:
        hist['date'] = pd.to_datetime(hist['date'])
        fig_h = px.area(hist, x='date', y='followers', template="plotly_dark")
        fig_h.update_layout(paper_bgcolor="black", plot_bgcolor="black", font_color="white")
        fig_h.update_traces(line_color="white", fillcolor="rgba(255,255,255,0.1)")
        st.plotly_chart(fig_h, use_container_width=True)
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.caption("No timeline data yet.")
