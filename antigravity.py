import streamlit as st
import pandas as pd
import requests
import toml
import plotly.express as px
import os
from datetime import datetime
from supabase import create_client, Client
import google.generativeai as genai

# --- SETUP & ANTIGRAVITY CSS ---
st.set_page_config(page_title="Creator Deck", layout="wide", page_icon="⚫")

def inject_antigravity_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;900&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
            background-color: #000000;
            color: #ffffff;
        }
        header {visibility: hidden;}
        
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #000000;
            border: none;
            box-shadow: none;
            padding: 0px;
        }
        
        [data-testid="stMetricValue"] {
            font-family: 'Inter', sans-serif;
            font-size: 3rem !important;
            font-weight: 900 !important;
            color: #ffffff !important;
            line-height: 1.2;
            letter-spacing: -1px;
        }
        
        [data-testid="stMetricLabel"] {
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #666666 !important;
        }

        .stButton > button {
            background-color: transparent;
            color: white;
            border: 1px solid #333;
            border-radius: 30px;
            padding: 10px 24px;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            border-color: #ffffff;
            background-color: #ffffff;
            color: #000000;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            border-bottom: 1px solid #222;
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            background-color: transparent;
            color: #666;
            font-weight: 500;
            font-size: 1rem;
            border: none;
        }
        .stTabs [aria-selected="true"] {
            color: #ffffff !important;
            background-color: transparent !important;
            border-bottom: 2px solid #ffffff !important;
        }
        
        /* AI Box Styling */
        .ai-box {
            border-left: 2px solid #ffffff;
            padding-left: 20px;
            margin-top: 20px;
            color: #cccccc;
        }

        img {
            border-radius: 8px;
            transition: opacity 0.3s;
        }
        img:hover {
            opacity: 0.8;
        }
    </style>
    """, unsafe_allow_html=True)

inject_antigravity_css()

# --- CONFIG & INIT ---
# Versucht erst st.secrets (Cloud/Lokal auto), Fallback auf manuelles Laden
try:
    if "SUPABASE_URL" in st.secrets:
        config = st.secrets
    else:
        config = toml.load("secrets.toml")
except (FileNotFoundError, AttributeError):
    st.error("Keine Secrets gefunden. Bitte in Streamlit Cloud unter Settings > Secrets eintragen.")
    st.stop()

# API Params
BASE_URL = f"https://graph.facebook.com/{config['API_VERSION']}/"
PARAMS = {'access_token': config['PAGE_ACCESS_TOKEN']}

# Supabase Client Init
@st.cache_resource
def init_supabase():
    url = config["SUPABASE_URL"]
    key = config["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Gemini Init
genai.configure(api_key=config["GEMINI_API_KEY"])

# --- DATA FETCHING (Instagram) ---
@st.cache_data(ttl=600)
def fetch_live_data():
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

# --- DATA FETCHING (Supabase) ---
def save_snapshot_supabase(fol, med, eng):
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"date": today, "followers": fol, "media_count": med, "avg_engagement": eng}
    try:
        supabase.table("instagram_history").upsert(data, on_conflict="date").execute()
        st.toast("Snapshot to Supabase saved.", icon="⚫")
    except Exception as e:
        st.error(f"Supabase Error: {e}")

def load_history_supabase():
    try:
        response = supabase.table("instagram_history").select("*").order("date").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- AI ANALYST ---
def run_ai_analysis(df_input):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Daten für Prompt vorbereiten (CSV String)
    csv_data = df_input[['Datum', 'Typ', 'Reichweite', 'Engagement', 'Caption']].to_csv(index=False)
    
    prompt = f"""
    Act as a senior social media strategist. Analyze this Instagram data:
    {csv_data}

    1. Identify the top performing content type and time.
    2. Spot one critical weakness or missed opportunity.
    3. Give me one concrete, 1-sentence action to take for the next post.
    
    Keep it extremely brief, bullet points, no fluff.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- RENDER ---
prof, posts = fetch_live_data()
if 'error' in prof: st.error(prof['error']['message']); st.stop()

df = pd.DataFrame(posts)
fol = prof.get('followers_count', 0)
if not df.empty: df['ER'] = round((df['Engagement'] / fol) * 100, 2)

# Sidebar
with st.sidebar:
    st.markdown("### ACCOUNT")
    st.caption(f"@{prof.get('username')}")
    st.metric("Follower", fol)
    st.divider()
    if st.button("SNAPSHOT"):
        avg = int(df['Engagement'].mean()) if not df.empty else 0
        save_snapshot_supabase(fol, prof.get('media_count'), avg)

# Main
st.title("ANTIGRAVITY DECK")
st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True) 

t1, t2, t3 = st.tabs(["VISUALS", "DATA + AI", "TIMELINE"])

with t1:
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("REACH", int(df['Reichweite'].mean()))
        c2.metric("LIKES", int(df['Likes'].mean()))
        c3.metric("ER RATE", f"{round(df['ER'].mean(), 2)}%")
        c4.metric("PEAK", int(df['Reichweite'].max()))
        
        st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
        
        cols_per_row = 3
        for i in range(0, len(df), cols_per_row):
            cols = st.columns(cols_per_row)
            batch = df.iloc[i:i+cols_per_row]
            for col, (_, row) in zip(cols, batch.iterrows()):
                with col:
                    if row['Image_URL']: st.image(row['Image_URL'], use_container_width=True)
                    mc1, mc2 = st.columns(2)
                    mc1.caption(f"REACH {row['Reichweite']}")
                    mc2.caption(f"LIKES {row['Likes']}")
    else:
        st.info("No posts yet. Post on Instagram to see data here.")

with t2:
    if not df.empty:
        # AI Section
        c_ai, c_chart = st.columns([1, 2])
        
        with c_ai:
            st.markdown("##### AI STRATEGIST")
            if st.button("ANALYZE DATA ⚡"):
                with st.spinner("Thinking..."):
                    analysis = run_ai_analysis(df)
                    st.markdown(f"<div class='ai-box'>{analysis}</div>", unsafe_allow_html=True)
        
        with c_chart:
            st.markdown("##### METRICS")
            fig = px.line(df, x='Datum', y=['Reichweite', 'Impressions'], template="plotly_dark")
            fig.update_layout(paper_bgcolor="#000000", plot_bgcolor="#000000", font_color="#ffffff")
            fig.update_traces(line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df[['Datum', 'Typ', 'Reichweite', 'Likes', 'ER']].sort_values(by='Datum', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No data for analysis.")

with t3:
    hist = load_history_supabase()
    if not hist.empty:
        hist['date'] = pd.to_datetime(hist['date'])
        fig_h = px.area(hist, x='date', y='followers', template="plotly_dark")
        fig_h.update_layout(paper_bgcolor="#000000", plot_bgcolor="#000000", font_color="#ffffff")
        fig_h.update_traces(line_color="#ffffff", fillcolor="rgba(255,255,255,0.1)")
        st.plotly_chart(fig_h, use_container_width=True)
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.caption("No timeline data in Supabase yet.")
