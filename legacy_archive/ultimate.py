import streamlit as st
import pandas as pd
import requests
import toml
import plotly.express as px
import os
from datetime import datetime

# --- KONFIGURATION ---
try:
    config = toml.load("secrets.toml")
except FileNotFoundError:
    st.error("Fehler: 'secrets.toml' nicht gefunden.")
    st.stop()

BASE_URL = f"https://graph.facebook.com/{config['API_VERSION']}/"
PARAMS = {'access_token': config['PAGE_ACCESS_TOKEN']}
HISTORY_FILE = "data_history.csv"

# --- API FUNKTIONEN (Gecached) ---
@st.cache_data(ttl=600)
def fetch_live_data():
    # 1. Profil abrufen
    profile = requests.get(
        BASE_URL + config['IG_USER_ID'],
        params={**PARAMS, 'fields': 'username,name,followers_count,media_count,profile_picture_url'}
    ).json()

    if 'error' in profile:
        return profile, []

    # 2. Medien Liste abrufen (Limit 20)
    media_response = requests.get(
        BASE_URL + config['IG_USER_ID'] + "/media",
        params={**PARAMS, 'fields': 'id,caption,media_type,timestamp,like_count,comments_count,permalink,media_url,thumbnail_url', 'limit': 20}
    ).json()

    posts_data = []
    
    if 'data' in media_response:
        for post in media_response['data']:
            # 3. Insights pro Post (Deep Dive)
            # Wir holen Reach & Impressions für JEDEN Beitrag
            insight_metrics = "reach,impressions"
            reach = 0
            impressions = 0
            
            try:
                ins_resp = requests.get(
                    BASE_URL + post['id'] + "/insights", 
                    params={**PARAMS, 'metric': insight_metrics}
                ).json()
                
                if 'data' in ins_resp:
                    for metric in ins_resp['data']:
                        if metric['name'] == 'reach':
                            reach = metric['values'][0]['value']
                        elif metric['name'] == 'impressions':
                            impressions = metric['values'][0]['value']
            except:
                pass # Fehler bei Insights ignorieren (z.B. bei sehr alten Posts)

            # Bild-URL Logik (Video vs Bild)
            image_url = post.get('thumbnail_url', post.get('media_url', ''))
            
            # Engagement Berechnung
            engagement = post.get('like_count', 0) + post.get('comments_count', 0)

            posts_data.append({
                'ID': post['id'],
                'Datum': pd.to_datetime(post['timestamp']),
                'Typ': post['media_type'],
                'Caption': post.get('caption', '')[:80] + "...",
                'Likes': post.get('like_count', 0),
                'Kommentare': post.get('comments_count', 0),
                'Reichweite': reach,
                'Impressions': impressions,
                'Engagement': engagement,
                'Image_URL': image_url,
                'Link': post.get('permalink')
            })

    return profile, posts_data

# --- HISTORY FUNKTIONEN ---
def save_snapshot(followers, media_count, avg_engagement):
    today = datetime.now().strftime("%Y-%m-%d")
    new_row = {'Datum': today, 'Follower': followers, 'Beiträge': media_count, 'Ø_Engagement': avg_engagement}
    
    if os.path.exists(HISTORY_FILE):
        df_hist = pd.read_csv(HISTORY_FILE)
        if today in df_hist['Datum'].astype(str).values:
            st.toast("Daten für heute sind schon gespeichert!", icon="ℹ️")
            return
    else:
        df_hist = pd.DataFrame(columns=['Datum', 'Follower', 'Beiträge', 'Ø_Engagement'])
    
    df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
    df_hist.to_csv(HISTORY_FILE, index=False)
    st.toast("Snapshot erfolgreich gespeichert!", icon="✅")

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()

# --- DASHBOARD LAYOUT ---
st.set_page_config(page_title="Creator Deck Ultimate", layout="wide")

# Daten laden
profile_json, posts_list = fetch_live_data()

if 'error' in profile_json:
    st.error(f"API Fehler: {profile_json['error']['message']}")
    st.stop()

followers = profile_json.get('followers_count', 1)
df_live = pd.DataFrame(posts_list)

# Berechne ER (%) falls Daten vorhanden
if not df_live.empty:
    df_live['ER (%)'] = round((df_live['Engagement'] / followers) * 100, 2)

# Sidebar
with st.sidebar:
    if 'profile_picture_url' in profile_json:
        st.image(profile_json['profile_picture_url'], width=80)
    st.header(f"@{profile_json.get('username')}")
    st.metric("Follower", followers)
    st.metric("Beiträge", profile_json.get('media_count'))
    st.divider()
    
    # Speicher-Button
    avg_eng = int(df_live['Engagement'].mean()) if not df_live.empty else 0
    if st.button("💾 Tages-Snapshot speichern"):
        save_snapshot(followers, profile_json.get('media_count'), avg_eng)

# Hauptbereich: 3 Tabs für ALLES
tab1, tab2, tab3 = st.tabs(["📸 Galerie", "📊 Live-Analyse", "📈 Historie"])

# --- TAB 1: GALERIE (VISUALS) ---
with tab1:
    st.subheader("Content Übersicht")
    if not df_live.empty:
        # KPI Header
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ø Reichweite", int(df_live['Reichweite'].mean()))
        c2.metric("Ø Likes", int(df_live['Likes'].mean()))
        c3.metric("Ø Engagement Rate", f"{round(df_live['ER (%)'].mean(), 2)}%")
        c4.metric("Top Post (Reach)", int(df_live['Reichweite'].max()))
        st.divider()

        # Grid View
        cols_per_row = 3
        for i in range(0, len(df_live), cols_per_row):
            cols = st.columns(cols_per_row)
            batch = df_live.iloc[i:i+cols_per_row]
            for col, (_, row) in zip(cols, batch.iterrows()):
                with col:
                    with st.container(border=True):
                        if row['Image_URL']:
                            st.image(row['Image_URL'], use_container_width=True)
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("👁️", row['Reichweite'])
                        m2.metric("❤️", row['Likes'])
                        m3.metric("💬", row['Kommentare'])
                        
                        st.caption(f"{row['Datum'].strftime('%d.%m.%Y')} | {row['Typ']}")
                        st.link_button("Zum Post", row['Link'])
    else:
        st.info("Keine Beiträge gefunden.")

# --- TAB 2: LIVE-ANALYSE (CHARTS & TABELLE) ---
with tab2:
    st.subheader("Deep Dive Analytics (Letzte 20 Beiträge)")
    if not df_live.empty:
        # Chart 1: Reichweite vs Impressions
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("**Sichtbarkeit über Zeit**")
            fig_reach = px.line(df_live, x='Datum', y=['Reichweite', 'Impressions'], markers=True)
            st.plotly_chart(fig_reach, use_container_width=True)
        
        with c2:
            st.write("**Verteilung nach Typ**")
            fig_pie = px.pie(df_live, values='Engagement', names='Typ', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Datentabelle (Rohdaten)
        st.write("**Detaillierte Datentabelle**")
        st.dataframe(
            df_live[['Datum', 'Typ', 'Reichweite', 'Impressions', 'Likes', 'Kommentare', 'ER (%)', 'Caption']].sort_values(by='Datum', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Keine Daten für Analyse.")

# --- TAB 3: HISTORIE (LANGZEIT) ---
with tab3:
    st.subheader("Wachstums-Verlauf (Gespeichert)")
    df_history = load_history()
    
    if not df_history.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Follower Wachstum**")
            fig_fol = px.area(df_history, x='Datum', y='Follower', markers=True)
            st.plotly_chart(fig_fol, use_container_width=True)
        with col_b:
            st.write("**Engagement Trend**")
            fig_eng = px.line(df_history, x='Datum', y='Ø_Engagement', markers=True)
            st.plotly_chart(fig_eng, use_container_width=True)
            
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("Noch keine Historie vorhanden. Nutzen Sie den Button in der Sidebar.")
