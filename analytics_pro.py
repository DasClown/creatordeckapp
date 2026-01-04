import streamlit as st
import pandas as pd
import requests
import toml
import plotly.express as px

# --- KONFIGURATION ---
try:
    config = toml.load("secrets.toml")
except FileNotFoundError:
    st.error("Fehler: 'secrets.toml' nicht gefunden.")
    st.stop()

BASE_URL = f"https://graph.facebook.com/{config['API_VERSION']}/"
PARAMS = {'access_token': config['PAGE_ACCESS_TOKEN']}

# --- API FUNKTIONEN ---
@st.cache_data(ttl=600)
def fetch_data():
    """
    Holt Profil, Medien und detaillierte Insights in einem Durchlauf.
    Limitierung auf die letzten 20 Beiträge, um API-Limits zu schonen.
    """
    # 1. Profil
    profile = requests.get(
        BASE_URL + config['IG_USER_ID'],
        params={**PARAMS, 'fields': 'username,name,followers_count,media_count,profile_picture_url'}
    ).json()

    if 'error' in profile:
        return profile, []

    # 2. Medien Liste (IDs holen)
    media_response = requests.get(
        BASE_URL + config['IG_USER_ID'] + "/media",
        params={**PARAMS, 'fields': 'id,caption,media_type,timestamp,like_count,comments_count,permalink', 'limit': 20}
    ).json()

    posts_data = []
    
    if 'data' in media_response:
        for post in media_response['data']:
            # 3. Insights pro Post abfragen (N+1 Problem)
            # Hinweis: Metriken unterscheiden sich je nach Medientyp leicht. 
            # Hier: Standard für Image/Video/Album.
            insight_metrics = "reach,impressions"
            
            # Bei Reels (VIDEO) funktionieren Impressions oft nicht, dafür 'plays'. 
            # Wir versuchen den Standard-Abruf, Fehler werden abgefangen.
            
            insights_url = BASE_URL + post['id'] + "/insights"
            i_params = {**PARAMS, 'metric': insight_metrics}
            
            try:
                ins_resp = requests.get(insights_url, params=i_params).json()
                
                # Werte extrahieren
                reach = 0
                impressions = 0
                
                if 'data' in ins_resp:
                    for metric in ins_resp['data']:
                        if metric['name'] == 'reach':
                            reach = metric['values'][0]['value']
                        elif metric['name'] == 'impressions':
                            impressions = metric['values'][0]['value']
            except:
                reach = 0
                impressions = 0

            # Datensatz bauen
            posts_data.append({
                'ID': post['id'],
                'Datum': pd.to_datetime(post['timestamp']),
                'Typ': post['media_type'],
                'Caption': post.get('caption', '')[:50] + "...",
                'Likes': post.get('like_count', 0),
                'Kommentare': post.get('comments_count', 0),
                'Reichweite': reach,
                'Impressions': impressions,
                'Engagement': post.get('like_count', 0) + post.get('comments_count', 0)
            })

    return profile, posts_data

# --- DASHBOARD LOGIK ---
st.set_page_config(page_title="IG Analytics Pro", layout="wide")

profile_json, posts_list = fetch_data()

if 'error' in profile_json:
    st.error(f"API Fehler: {profile_json['error']['message']}")
    st.stop()

# DataFrame erstellen
df = pd.DataFrame(posts_list)
followers = profile_json.get('followers_count', 1)

# Berechnung KPIs
if not df.empty:
    df['ER (%)'] = round((df['Engagement'] / followers) * 100, 2)

# --- VISUALISIERUNG ---

# Sidebar
with st.sidebar:
    if 'profile_picture_url' in profile_json:
        st.image(profile_json['profile_picture_url'], width=80)
    st.header(f"@{profile_json.get('username')}")
    st.metric("Follower", followers)
    st.metric("Media Count", profile_json.get('media_count'))

# Main
st.title("📈 Deep Dive Analytics")

if df.empty:
    st.info("Keine Daten verfügbar oder Konto ist neu.")
    st.stop()

# 1. Performance Overview
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg. Reichweite", int(df['Reichweite'].mean()))
col2.metric("Avg. Impressions", int(df['Impressions'].mean()))
col3.metric("Avg. Engagement", int(df['Engagement'].mean()))
col4.metric("Avg. ER", f"{round(df['ER (%)'].mean(), 2)}%")

st.divider()

# 2. Charts
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Reichweite vs. Impressions")
    # Dual-Line Chart
    fig_reach = px.line(df, x='Datum', y=['Reichweite', 'Impressions'], markers=True, 
                        title="Sichtbarkeit über Zeit")
    st.plotly_chart(fig_reach, use_container_width=True)

with c2:
    st.subheader("Engagement nach Typ")
    fig_pie = px.pie(df, values='Engagement', names='Typ', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# 3. Detail-Tabelle (Interaktiv)
st.subheader("Post Details")
st.dataframe(
    df[['Datum', 'Typ', 'Reichweite', 'Impressions', 'Likes', 'Kommentare', 'ER (%)', 'Caption']].sort_values(by='Datum', ascending=False),
    use_container_width=True,
    hide_index=True
)
