"""
API CONNECTIONS MANAGER
Sichere Verwaltung von API-Tokens für Platform-Integrationen
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_api_connections(supabase):
    """Rendert API Connections Manager."""
    st.title("🔑 API CONNECTIONS")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    st.info("""
    **Sichere Token-Verwaltung**
    
    Speichere API-Tokens für direkte Platform-Integrationen.
    Tokens werden verschlüsselt in der Datenbank gespeichert.
    """)
    
    # Bestehende Connections
    st.markdown("### 🔗 ACTIVE CONNECTIONS")
    
    connections = supabase.table("api_connections")\
        .select("*")\
        .eq("user_id", user_email)\
        .order("created_at", desc=True)\
        .execute()
    
    if connections.data and len(connections.data) > 0:
        df_conn = pd.DataFrame(connections.data)
        
        # Mask Tokens
        df_conn['api_token_masked'] = df_conn['api_token'].apply(
            lambda x: f"{x[:8]}...{x[-4:]}" if len(x) > 12 else "***"
        )
        
        df_conn['created_at'] = pd.to_datetime(df_conn['created_at']).dt.strftime('%Y-%m-%d')
        df_conn['last_used'] = pd.to_datetime(df_conn['last_used']).dt.strftime('%Y-%m-%d %H:%M')
        
        display_cols = ['platform', 'api_token_masked', 'token_type', 'is_active', 'last_used', 'created_at']
        available_cols = [col for col in display_cols if col in df_conn.columns]
        
        st.dataframe(
            df_conn[available_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Delete Connection
        with st.expander("🗑️ DELETE CONNECTION"):
            platform_to_delete = st.selectbox(
                "Platform",
                df_conn['platform'].tolist(),
                key="delete_platform"
            )
            
            if st.button("DELETE", type="primary"):
                try:
                    supabase.table("api_connections")\
                        .delete()\
                        .eq("user_id", user_email)\
                        .eq("platform", platform_to_delete)\
                        .execute()
                    st.success(f"✅ {platform_to_delete} connection deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("💡 Keine API-Connections vorhanden. Füge unten eine hinzu.")
    
    # Add New Connection
    st.markdown("---")
    st.markdown("### ➕ ADD NEW CONNECTION")
    
    col1, col2 = st.columns(2)
    
    with col1:
        platform = st.selectbox(
            "Platform",
            ["Fansly", "OnlyFans", "TikTok", "Instagram", "YouTube"],
            key="new_platform"
        )
        
        api_token = st.text_input(
            "API Token",
            type="password",
            help="Dein API-Token von der Platform",
            key="new_token"
        )
    
    with col2:
        token_type = st.selectbox(
            "Token Type",
            ["Bearer", "Binding", "OAuth"],
            key="new_token_type"
        )
        
        expires_days = st.number_input(
            "Expires in (days)",
            min_value=0,
            value=365,
            help="0 = never expires",
            key="new_expires"
        )
    
    if st.button("ADD CONNECTION", use_container_width=True):
        if api_token:
            try:
                expires_at = None
                if expires_days > 0:
                    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
                
                supabase.table("api_connections").insert({
                    "user_id": user_email,
                    "platform": platform.lower(),
                    "api_token": api_token,
                    "token_type": token_type,
                    "expires_at": expires_at,
                    "is_active": True
                }).execute()
                
                st.success(f"✅ {platform} connection added!")
                st.rerun()
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    st.error(f"❌ Connection für {platform} existiert bereits. Lösche die alte zuerst.")
                else:
                    st.error(f"Error: {e}")
        else:
            st.warning("API Token erforderlich")
    
    # Platform-Specific Guides
    st.markdown("---")
    st.markdown("### 📚 PLATFORM GUIDES")
    
    with st.expander("🔞 FANSLY API TOKEN"):
        st.markdown("""
        **So erhältst du deinen Fansly API-Token:**
        
        1. Gehe zu Fansly Settings → Developer
        2. Erstelle einen neuen API-Key
        3. Kopiere den Token (wird nur einmal angezeigt!)
        4. Token-Type: **Binding**
        
        **Berechtigungen:** Account Stats, Follower Count
        """)
    
    with st.expander("🔞 ONLYFANS API TOKEN"):
        st.markdown("""
        **OnlyFans API-Zugang:**
        
        OnlyFans bietet keine offizielle API.
        Nutze stattdessen den Worker-Service im OnlyFans-Modul.
        """)
    
    with st.expander("📱 TIKTOK API TOKEN"):
        st.markdown("""
        **TikTok Business API:**
        
        1. Registriere dich bei TikTok for Developers
        2. Erstelle eine App
        3. Generiere Access Token
        4. Token-Type: **Bearer**
        """)
