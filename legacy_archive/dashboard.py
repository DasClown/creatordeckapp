import streamlit as st
import pandas as pd
import requests
import toml
import plotly.express as px

# Konfiguration laden
try:
    config = toml.load("secrets.toml")
except FileNotFoundError:
    st.error("Fehler: 'secrets.toml' nicht gefunden.")
    st.stop()

# API Funktionen (Gecached)
@st.cache_data(ttl=300) # Daten werden für 5 Minuten gespeichert
def fetch_instagram_data():
    base_url = f"https://graph.facebook.com/{config['API_VERSION']}/"
    params = {'access_token': config['PAGE_ACCESS_TOKEN']}
    
    # 1. Profil
    profile_url = base_url + config['IG_USER_ID']
    p_params = params.copy()
    p_params['fields'] = 'username,name,followers_count,media_count,biography,profile_picture_url'
    profile = requests.get(profile_url, params=p_params).json()
    
    # 2. Media
    media_url = base_url + config['IG_USER_ID'] + "/media"
    m_params = params.copy()
    m_params['fields'] = 'id,caption,media_type,timestamp,like_count,comments_count,permalink'
    m_params['limit'] = 50
    media = requests.get(media_url, params=m_params).json()
    
    return profile, media

# Daten verarbeiten
def process_data(media_json, followers):
    if 'data' not in media_json:
        return pd.DataFrame()
        
    posts = []
    for item in media_json['data']:
        likes = item.get('like_count', 0)
        comments = item.get('comments_count', 0)
        engagement = likes + comments
        er = (engagement / followers * 100) if followers > 0 else 0
        
        posts.append({
            'Datum': pd.to_datetime(item['timestamp']),
            'Typ': item['media_type'],
            'Likes': likes,
            'Kommentare': comments,
            'Engagement': engagement,
            'ER (%)': round(er, 2),
            'Caption': item.get('caption', '')
        })
    
    return pd.DataFrame(posts)

# --- DASHBOARD LAYOUT ---
st.set_page_config(page_title="Creator Deck", layout="wide")

# Daten laden
try:
    profile_data, media_data = fetch_instagram_data()
except Exception as e:
    st.error(f"API Fehler: {e}")
    st.stop()

if 'error' in profile_data:
    st.error(f"API Error: {profile_data['error']['message']}")
    st.stop()

followers = profile_data.get('followers_count', 1)
df = process_data(media_data, followers)

# Sidebar: Profil Info
with st.sidebar:
    if 'profile_picture_url' in profile_data:
        st.image(profile_data['profile_picture_url'], width=100)
    st.title(f"@{profile_data.get('username')}")
    st.write(profile_data.get('biography'))
    st.divider()
    st.metric("Follower", followers)
    st.metric("Beiträge", profile_data.get('media_count'))

# Hauptbereich
st.title("📊 Performance Dashboard")

if not df.empty:
    # Top-Level KPIs
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Durchschn. Likes", round(df['Likes'].mean(), 1))
    kpi2.metric("Durchschn. ER", f"{round(df['ER (%)'].mean(), 2)}%")
    kpi3.metric("Top Post (Likes)", df['Likes'].max())

    st.divider()

    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Entwicklung Likes")
        fig_line = px.line(df, x='Datum', y='Likes', markers=True, title="Likes über Zeit")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col2:
        st.subheader("Performance nach Typ")
        fig_bar = px.box(df, x='Typ', y='ER (%)', title="Engagement Rate Verteilung")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabelle
    st.subheader("Datensatz")
    st.dataframe(df.sort_values(by='Datum', ascending=False), use_container_width=True)

else:
    st.info("Keine Beitragsdaten verfügbar.")
