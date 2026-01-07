"""
YOUTUBE ANALYTICS MODULE
OAuth-basierte YouTube-Daten-Synchronisierung
"""

import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta

# Client-Konfiguration aus den Secrets
def get_client_config():
    """Erstellt Google OAuth Client Config aus Secrets."""
    try:
        return {
            "web": {
                "client_id": st.secrets.get("GOOGLE_CLIENT_ID", ""),
                "client_secret": st.secrets.get("GOOGLE_CLIENT_SECRET", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets.get("GOOGLE_REDIRECT_URI", "https://content-core.com")]
            }
        }
    except Exception:
        return None

# OAuth Scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]

def init_oauth_flow():
    """Initialisiert OAuth Flow."""
    try:
        flow = Flow.from_client_config(
            get_client_config(),
            scopes=SCOPES,
            redirect_uri=st.secrets.get("GOOGLE_REDIRECT_URI", "https://content-core.com")
        )
        return flow
    except Exception as e:
        st.error(f"OAuth Flow Error: {e}")
        return None

def get_youtube_service(credentials):
    """Erstellt YouTube API Service."""
    try:
        return build('youtube', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"YouTube Service Error: {e}")
        return None

def get_youtube_analytics_service(credentials):
    """Erstellt YouTube Analytics API Service."""
    try:
        return build('youtubeAnalytics', 'v2', credentials=credentials)
    except Exception as e:
        st.error(f"YouTube Analytics Service Error: {e}")
        return None

def sync_youtube_data(credentials, supabase):
    """
    Synchronisiert YouTube-Daten.
    
    Args:
        credentials: Google OAuth Credentials
        supabase: Supabase Client
    
    Returns:
        bool: True bei Erfolg
    """
    try:
        user_email = st.session_state.get('user_email', 'unknown')
        
        # YouTube Service
        youtube = get_youtube_service(credentials)
        if not youtube:
            return False
        
        # Channel Info abrufen
        channels_response = youtube.channels().list(
            part='snippet,statistics',
            mine=True
        ).execute()
        
        if not channels_response.get('items'):
            st.error("Kein YouTube-Kanal gefunden")
            return False
        
        channel = channels_response['items'][0]
        stats = channel['statistics']
        snippet = channel['snippet']
        
        # Daten extrahieren
        channel_title = snippet.get('title', 'Unknown')
        subscribers = int(stats.get('subscriberCount', 0))
        total_views = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 0))
        
        # In stats_history speichern
        from app import calculate_growth
        
        stats_payload = {
            "user_id": user_email,
            "platform": "youtube",
            "handle": channel_title,
            "followers": subscribers,
            "video_views": total_views,
            "subscriber_count": subscribers,
            "net_growth": calculate_growth(subscribers, "youtube", channel_title)
        }
        
        supabase.table("stats_history").insert(stats_payload).execute()
        
        st.success(f"✅ YouTube Sync erfolgreich: {subscribers:,} Subscribers")
        return True
        
    except Exception as e:
        st.error(f"YouTube Sync Error: {e}")
        return False

def render_youtube_analytics(supabase):
    """Rendert YouTube Analytics Dashboard."""
    st.title("📺 YOUTUBE ANALYTICS")
    
    # Check if Google OAuth Secrets are configured
    if not st.secrets.get("GOOGLE_CLIENT_ID") or not st.secrets.get("GOOGLE_CLIENT_SECRET"):
        st.error("❌ Google OAuth nicht konfiguriert")
        st.info("""
        **Setup erforderlich:**
        
        Füge folgende Secrets zu `.streamlit/secrets.toml` hinzu:
        
        ```toml
        GOOGLE_CLIENT_ID = "1041446795210-j87qs4vv2pvapbirmg6leose7g362mms.apps.googleusercontent.com"
        GOOGLE_CLIENT_SECRET = "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"
        GOOGLE_REDIRECT_URI = "https://content-core.com"
        ```
        
        **Streamlit Cloud:**
        - App Settings → Secrets
        - Füge die 3 Zeilen oben ein
        - Save & Deploy
        """)
        return
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    st.info("""
    **YouTube OAuth Integration**
    
    Verbinde deinen YouTube-Kanal für automatische Analytics-Synchronisierung.
    Benötigt Google OAuth-Authentifizierung.
    """)
    
    # OAuth Status Check
    if 'youtube_credentials' not in st.session_state:
        st.session_state.youtube_credentials = None
    
    # OAuth Flow
    if st.session_state.youtube_credentials is None:
        st.markdown("### 🔐 YOUTUBE VERBINDEN")
        
        if st.button("CONNECT YOUTUBE", use_container_width=True):
            flow = init_oauth_flow()
            if flow:
                # Authorization URL generieren
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                st.markdown(f"""
                **Schritt 1:** Klicke auf den Link unten
                
                [{auth_url}]({auth_url})
                
                **Schritt 2:** Autorisiere die App
                
                **Schritt 3:** Kopiere den Code und füge ihn unten ein
                """)
                
                auth_code = st.text_input("Authorization Code", key="yt_auth_code")
                
                if st.button("AUTHORIZE", use_container_width=True):
                    if auth_code:
                        try:
                            flow.fetch_token(code=auth_code)
                            st.session_state.youtube_credentials = flow.credentials
                            st.success("✅ YouTube verbunden!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Authorization Error: {e}")
                    else:
                        st.warning("Authorization Code erforderlich")
    else:
        st.success("✅ YouTube ist verbunden")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("SYNC NOW", use_container_width=True):
                if sync_youtube_data(st.session_state.youtube_credentials, supabase):
                    st.rerun()
        
        with col2:
            if st.button("DISCONNECT", use_container_width=True):
                st.session_state.youtube_credentials = None
                st.rerun()
        
        # YouTube Stats anzeigen
        st.markdown("---")
        st.markdown("### 📊 YOUTUBE STATS")
        
        try:
            stats = supabase.table("stats_history")\
                .select("*")\
                .eq("user_id", user_email)\
                .eq("platform", "youtube")\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if stats.data and len(stats.data) > 0:
                df = pd.DataFrame(stats.data)
                
                # KPIs
                latest = df.iloc[0]
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("SUBSCRIBERS", f"{int(latest.get('followers', 0)):,}")
                col2.metric("TOTAL VIEWS", f"{int(latest.get('video_views', 0)):,}")
                col3.metric("NET GROWTH", f"{int(latest.get('net_growth', 0)):,}")
                col4.metric("SYNCS", len(df))
                
                # History Table
                st.markdown("#### 📜 SYNC HISTORY")
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                display_cols = ['created_at', 'followers', 'video_views', 'net_growth']
                available_cols = [col for col in display_cols if col in df.columns]
                
                st.dataframe(
                    df[available_cols],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("💡 Noch keine YouTube-Daten. Klicke 'SYNC NOW' oben.")
        except Exception as e:
            st.error(f"Stats Error: {e}")
