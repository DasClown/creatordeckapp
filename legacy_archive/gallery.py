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
    # 1. Profil
    profile = requests.get(
        BASE_URL + config['IG_USER_ID'],
        params={**PARAMS, 'fields': 'username,name,followers_count,media_count,profile_picture_url'}
    ).json()

    if 'error' in profile:
        return profile, []

    # 2. Medien Liste
    media_response = requests.get(
        BASE_URL + config['IG_USER_ID'] + "/media",
        params={**PARAMS, 'fields': 'id,caption,media_type,timestamp,like_count,comments_count,permalink,media_url,thumbnail_url', 'limit': 20}
    ).json()

    posts_data = []
    
    if 'data' in media_response:
        for post in media_response['data']:
            # Insights pro Post
            insight_metrics = "reach,impressions"
            try:
                ins_resp = requests.get(
                    BASE_URL + post['id'] + "/insights", 
                    params={**PARAMS, 'metric': insight_metrics}
                ).json()
                
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

            # Bild-URL wählen (Video hat 'thumbnail_url', Bild hat 'media_url')
            image_url = post.get('thumbnail_url', post.get('media_url', ''))

            posts_data.append({
                'ID': post['id'],
                'Datum': pd.to_datetime(post['timestamp']),
                'Typ': post['media_type'],
                'Caption': post.get('caption', '')[:80] + "...", # Etwas mehr Text
                'Likes': post.get('like_count', 0),
                'Kommentare': post.get('comments_count', 0),
                'Reichweite': reach,
                'Impressions': impressions,
                'Engagement': post.get('like_count', 0) + post.get('comments_count', 0),
                'Image_URL': image_url,
                'Link': post.get('permalink')
            })

    return profile, posts_data

# --- DASHBOARD LOGIK ---
st.set_page_config(page_title="Creator Deck Visual", layout="wide")

profile_json, posts_list = fetch_data()

if 'error' in profile_json:
    st.error(f"API Fehler: {profile_json['error']['message']}")
    st.stop()

followers = profile_json.get('followers_count', 1)
df = pd.DataFrame(posts_list)

# Sidebar
with st.sidebar:
    if 'profile_picture_url' in profile_json:
        st.image(profile_json['profile_picture_url'], width=80)
    st.header(f"@{profile_json.get('username')}")
    st.metric("Follower", followers)
    st.metric("Beiträge", profile_json.get('media_count'))

st.title("📸 Content Gallery")

if df.empty:
    st.info("Keine Beiträge gefunden. Posten Sie etwas auf Instagram, um hier Daten zu sehen.")
    st.stop()

# --- KPI HEADER ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ø Reichweite", int(df['Reichweite'].mean()))
col2.metric("Ø Likes", int(df['Likes'].mean()))
col3.metric("Gesamt Engagement", int(df['Engagement'].sum()))
col4.metric("Top Post (Reach)", int(df['Reichweite'].max()))

st.divider()

# --- VISUAL GALLERY GRID ---
st.subheader("Neueste Beiträge")

# Wir erstellen Zeilen mit je 3 Spalten
cols_per_row = 3
for i in range(0, len(df), cols_per_row):
    cols = st.columns(cols_per_row)
    # Slice des Dataframes für die aktuelle Zeile
    batch = df.iloc[i:i+cols_per_row]
    
    for col, (_, row) in zip(cols, batch.iterrows()):
        with col:
            # Karte / Container
            with st.container(border=True):
                # Bild anzeigen
                if row['Image_URL']:
                    st.image(row['Image_URL'], use_container_width=True)
                
                # Metriken kompakt unter dem Bild
                c1, c2, c3 = st.columns(3)
                c1.metric("👁️", row['Reichweite'])
                c2.metric("❤️", row['Likes'])
                c3.metric("💬", row['Kommentare'])
                
                st.caption(f"📅 {row['Datum'].strftime('%d.%m.%Y')}")
                st.text(row['Caption'])
                st.link_button("Zu Instagram", row['Link'])

st.divider()

# --- CHART VIEW (Optional unten) ---
with st.expander("Detaillierte Analyse ansehen"):
    st.subheader("Performance Matrix")
    fig = px.scatter(df, x="Reichweite", y="Likes", size="Engagement", hover_name="Typ", 
                     title="Reichweite vs. Likes (Bubble Size = Engagement)")
    st.plotly_chart(fig, use_container_width=True)
