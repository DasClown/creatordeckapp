"""
ONLYFANS SYNC & WHALE WATCHER MODULE
External Worker Integration + Customer Analytics
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

def trigger_of_sync(account_credentials, sync_type="full"):
    """
    Triggert externen Worker-Service für OnlyFans-Sync.
    
    WICHTIG: Direkter Login via Streamlit führt zur Account-Sperrung!
    Nutze einen dedizierten Worker-Service (z.B. auf Railway, Render, etc.)
    
    Args:
        account_credentials: Dict mit user, pw, 2fa
        sync_type: "full", "customers", "vault", "revenue"
    
    Returns:
        bool: True bei Erfolg
    """
    # TODO: Ersetze mit deinem Worker-Service-URL
    sync_url = "https://your-worker-service.com/sync"
    
    try:
        payload = {
            **account_credentials,
            "sync_type": sync_type,
            "user_id": st.session_state.get('user_email', 'unknown')
        }
        
        res = requests.post(sync_url, json=payload, timeout=30)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Worker Connection Error: {e}")
        return False

def display_sync_panel(supabase):
    """Rendert OnlyFans Sync Control Panel."""
    st.header("🔄 ONLYFANS FULL CORE SYNC")
    st.warning("⚠️ Nutzt externen Worker-Service. Direkter Login führt zur Sperrung!")
    
    st.info("""
    **Was wird synchronisiert:**
    - Follower & Subscriber Count
    - Content Vault (Posts, PPV)
    - Revenue History
    - Top Spender (Whale Watcher)
    """)
    
    with st.expander("🔐 CONNECTION SETTINGS"):
        of_mail = st.text_input("OnlyFans Email", key="of_email")
        of_pass = st.text_input("OnlyFans Password", type="password", key="of_pass")
        auth_2fa = st.text_input("2FA Secret (optional)", key="of_2fa", help="Falls 2FA aktiviert")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("START FULL SYNC", use_container_width=True):
                if of_mail and of_pass:
                    credentials = {
                        "user": of_mail,
                        "pw": of_pass,
                        "2fa": auth_2fa if auth_2fa else None
                    }
                    
                    # Log Sync Start
                    user_email = st.session_state.get('user_email', 'unknown')
                    supabase.table("of_sync_log").insert({
                        "user_id": user_email,
                        "sync_type": "full",
                        "status": "pending"
                    }).execute()
                    
                    if trigger_of_sync(credentials, "full"):
                        st.success("✅ Sync-Prozess gestartet. Daten erscheinen in Kürze.")
                    else:
                        st.error("❌ Verbindung fehlgeschlagen. Prüfe Credentials oder Worker-Service.")
                else:
                    st.warning("Email und Passwort erforderlich")
        
        with col2:
            if st.button("CUSTOMERS ONLY", use_container_width=True):
                st.info("Synchronisiert nur Kunden-Daten (schneller)")
    
    # Sync History
    st.markdown("---")
    st.markdown("### 📜 SYNC HISTORY")
    
    user_email = st.session_state.get('user_email', 'unknown')
    sync_history = supabase.table("of_sync_log")\
        .select("*")\
        .eq("user_id", user_email)\
        .order("started_at", desc=True)\
        .limit(10)\
        .execute()
    
    if sync_history.data:
        df_sync = pd.DataFrame(sync_history.data)
        df_sync['started_at'] = pd.to_datetime(df_sync['started_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            df_sync[['started_at', 'sync_type', 'status', 'items_synced']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Noch keine Syncs durchgeführt")

def display_whale_watcher(supabase):
    """Rendert Whale Watcher (Top Spender Analytics)."""
    st.header("🐋 WHALE WATCHER (TOP SPENDER)")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    # Top Spender aus View
    whales = supabase.table("whale_watcher")\
        .select("*")\
        .eq("user_id", user_email)\
        .limit(20)\
        .execute()
    
    if whales.data and len(whales.data) > 0:
        df_whales = pd.DataFrame(whales.data)
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        total_whale_revenue = df_whales['total_spent'].sum()
        whale_count = len(df_whales[df_whales['customer_tier'] == 'WHALE'])
        avg_whale_spend = df_whales[df_whales['customer_tier'] == 'WHALE']['total_spent'].mean() if whale_count > 0 else 0
        top_whale = df_whales.iloc[0]
        
        col1.metric("TOTAL WHALE REVENUE", f"${total_whale_revenue:,.2f}")
        col2.metric("WHALE COUNT", f"{whale_count}")
        col3.metric("AVG WHALE SPEND", f"${avg_whale_spend:,.2f}")
        col4.metric("TOP WHALE", top_whale['customer_username'], f"${top_whale['total_spent']:,.2f}")
        
        # Tier Breakdown
        st.markdown("---")
        st.markdown("### 🏆 CUSTOMER TIERS")
        
        tier_counts = df_whales['customer_tier'].value_counts()
        tier_cols = st.columns(4)
        
        tiers = ['WHALE', 'DOLPHIN', 'FISH', 'MINNOW']
        tier_emojis = {'WHALE': '🐋', 'DOLPHIN': '🐬', 'FISH': '🐟', 'MINNOW': '🐠'}
        
        for i, tier in enumerate(tiers):
            count = tier_counts.get(tier, 0)
            tier_cols[i].metric(f"{tier_emojis[tier]} {tier}", f"{count}")
        
        # Top Spender Table
        st.markdown("---")
        st.markdown("### 📊 TOP 20 SPENDER")
        
        display_cols = ['customer_username', 'customer_tier', 'total_spent', 'purchase_count', 'subscription_status']
        available_cols = [col for col in display_cols if col in df_whales.columns]
        
        st.dataframe(
            df_whales[available_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Add Customer Note
        with st.expander("📝 ADD CUSTOMER NOTE"):
            customer_select = st.selectbox(
                "Customer",
                df_whales['customer_username'].tolist(),
                key="whale_customer_select"
            )
            note_text = st.text_area("Note", key="whale_note")
            
            if st.button("SAVE NOTE"):
                if note_text:
                    try:
                        supabase.table("of_customers")\
                            .update({"notes": note_text})\
                            .eq("user_id", user_email)\
                            .eq("customer_username", customer_select)\
                            .execute()
                        st.success(f"✅ Note saved for {customer_select}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
    else:
        st.info("💡 Keine Kunden-Daten vorhanden. Führe einen OnlyFans-Sync durch.")
        st.markdown("**Hinweis:** Nutze den Sync-Panel oben, um Daten zu importieren.")

def render_onlyfans_analytics(supabase):
    """Main Render-Funktion für OnlyFans Analytics."""
    st.title("🔞 ONLYFANS ANALYTICS")
    
    # Check Adult Content Setting
    if not st.session_state.get('adult_content_enabled', False):
        st.warning("⚠️ Adult Content ist deaktiviert. Aktiviere es in den System Settings.")
        return
    
    # Tabs
    tab1, tab2 = st.tabs(["🐋 WHALE WATCHER", "🔄 SYNC CONTROL"])
    
    with tab1:
        display_whale_watcher(supabase)
    
    with tab2:
        display_sync_panel(supabase)
