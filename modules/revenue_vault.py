"""
REVENUE & VAULT ANALYTICS MODULE
Tracking für Umsatz und Medien-Performance
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_revenue_vault(supabase):
    """
    Rendert Revenue-Tracking und Vault-Analytics Dashboard.
    
    Features:
    - Quick Revenue Logging
    - Total Revenue Metrics
    - Platform Breakdown
    - Vault Asset Performance
    """
    st.title("💰 REVENUE & VAULT ANALYTICS")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    # Sidebar: Quick Log
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💵 QUICK LOG REVENUE")
        
        # Platform Selection (nur Adult-Plattformen wenn aktiviert)
        platforms = ["Instagram", "TikTok"]
        if st.session_state.get('adult_content_enabled', False):
            platforms.extend(["OnlyFans", "Fansly"])
        
        platform = st.selectbox("PLATFORM", platforms, key="rev_platform")
        amount_net = st.number_input("Net Amount ($)", min_value=0.0, step=10.0, key="rev_amount")
        source = st.selectbox("SOURCE", ["Subscription", "PPV", "Tips", "Sponsorship", "Ad Revenue"], key="rev_source")
        
        if st.button("LOG TRANSACTION", use_container_width=True):
            if amount_net > 0:
                try:
                    # Berechne Brutto (20% Fee)
                    fee_percentage = 20.0
                    amount_gross = amount_net / (1 - fee_percentage / 100)
                    
                    supabase.table("revenue_history").insert({
                        "user_id": user_email,
                        "platform": platform.lower(),
                        "amount_net": float(amount_net),
                        "amount_gross": float(amount_gross),
                        "fee_percentage": fee_percentage,
                        "source": source.lower(),
                        "currency": "USD"
                    }).execute()
                    
                    st.success(f"✅ ${amount_net:.2f} logged!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Amount must be > 0")
    
    # Main Dashboard
    try:
        # Revenue Metriken
        st.markdown("### 📊 REVENUE OVERVIEW")
        
        rev_res = supabase.table("revenue_history")\
            .select("*")\
            .eq("user_id", user_email)\
            .execute()
        
        if rev_res.data and len(rev_res.data) > 0:
            df_rev = pd.DataFrame(rev_res.data)
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            
            total_net = df_rev['amount_net'].sum()
            total_gross = df_rev['amount_gross'].sum() if 'amount_gross' in df_rev.columns else 0
            total_fees = total_gross - total_net
            transaction_count = len(df_rev)
            
            col1.metric("TOTAL NET REVENUE", f"${total_net:,.2f}")
            col2.metric("TOTAL GROSS", f"${total_gross:,.2f}")
            col3.metric("PLATFORM FEES", f"${total_fees:,.2f}")
            col4.metric("TRANSACTIONS", f"{transaction_count:,}")
            
            # Platform Breakdown
            st.markdown("---")
            st.markdown("### 💳 PLATFORM BREAKDOWN")
            
            platform_summary = df_rev.groupby('platform').agg({
                'amount_net': 'sum',
                'amount_gross': 'sum',
                'id': 'count'
            }).reset_index()
            platform_summary.columns = ['Platform', 'Net Revenue', 'Gross Revenue', 'Transactions']
            platform_summary = platform_summary.sort_values('Net Revenue', ascending=False)
            
            # Filter Adult-Content
            if not st.session_state.get('adult_content_enabled', False):
                platform_summary = platform_summary[~platform_summary['Platform'].isin(['onlyfans', 'fansly'])]
            
            if not platform_summary.empty:
                cols = st.columns(len(platform_summary))
                for i, row in platform_summary.iterrows():
                    cols[i].caption(row['Platform'].upper())
                    cols[i].metric("Net", f"${row['Net Revenue']:,.2f}")
                    cols[i].caption(f"{int(row['Transactions'])} transactions")
            
            # Recent Transactions
            st.markdown("---")
            st.markdown("### 📜 RECENT TRANSACTIONS")
            
            df_recent = df_rev.sort_values('created_at', ascending=False).head(10)
            df_recent['created_at'] = pd.to_datetime(df_recent['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            display_cols = ['created_at', 'platform', 'source', 'amount_net', 'amount_gross']
            available_cols = [col for col in display_cols if col in df_recent.columns]
            
            st.dataframe(
                df_recent[available_cols],
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.info("💡 No revenue data yet. Use the sidebar to log your first transaction!")
        
        # Vault Analytics
        st.markdown("---")
        st.markdown("### 🖼️ VAULT PERFORMANCE (TOP ASSETS)")
        
        vault_res = supabase.table("vault_assets")\
            .select("*")\
            .eq("user_id", user_email)\
            .order("total_revenue", desc=True)\
            .limit(20)\
            .execute()
        
        if vault_res.data and len(vault_res.data) > 0:
            df_vault = pd.DataFrame(vault_res.data)
            
            # Top Performers
            col1, col2 = st.columns(2)
            
            top_asset = df_vault.iloc[0]
            col1.metric(
                "TOP PERFORMER",
                top_asset['asset_name'],
                f"${top_asset['total_revenue']:,.2f}"
            )
            
            total_vault_revenue = df_vault['total_revenue'].sum()
            col2.metric("TOTAL VAULT REVENUE", f"${total_vault_revenue:,.2f}")
            
            # Vault Table
            st.markdown("#### 📊 ASSET BREAKDOWN")
            
            display_cols = ['asset_name', 'media_type', 'total_revenue', 'ppv_opens', 'likes', 'platform']
            available_cols = [col for col in display_cols if col in df_vault.columns]
            
            st.dataframe(
                df_vault[available_cols],
                use_container_width=True,
                hide_index=True
            )
            
            # Quick Add Asset
            with st.expander("➕ ADD NEW VAULT ASSET"):
                asset_name = st.text_input("Asset Name", placeholder="summer_beach_2024.jpg")
                media_type = st.selectbox("Media Type", ["image", "video", "audio"])
                platform_vault = st.selectbox("Platform", ["OnlyFans", "Fansly", "Instagram"])
                is_premium = st.checkbox("Premium Content")
                
                if st.button("ADD ASSET"):
                    if asset_name:
                        try:
                            supabase.table("vault_assets").insert({
                                "user_id": user_email,
                                "asset_name": asset_name,
                                "media_type": media_type,
                                "platform": platform_vault.lower(),
                                "is_premium": is_premium
                            }).execute()
                            st.success(f"✅ {asset_name} added to vault!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Asset name required")
        else:
            st.info("💡 No vault assets tracked yet. Add your first asset below!")
            
            # Quick Add (wenn keine Assets vorhanden)
            st.markdown("#### ➕ ADD YOUR FIRST ASSET")
            col1, col2 = st.columns(2)
            
            with col1:
                asset_name = st.text_input("Asset Name", placeholder="my_first_photo.jpg")
                media_type = st.selectbox("Media Type", ["image", "video", "audio"])
            
            with col2:
                platform_vault = st.selectbox("Platform", ["OnlyFans", "Fansly", "Instagram"])
                is_premium = st.checkbox("Premium Content")
            
            if st.button("ADD ASSET", use_container_width=True):
                if asset_name:
                    try:
                        supabase.table("vault_assets").insert({
                            "user_id": user_email,
                            "asset_name": asset_name,
                            "media_type": media_type,
                            "platform": platform_vault.lower(),
                            "is_premium": is_premium
                        }).execute()
                        st.success(f"✅ {asset_name} added to vault!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Asset name required")
        
    except Exception as e:
        st.error(f"ANALYTICS ERROR: {e}")
        st.info("💡 Make sure you've run the migration: migrations/004_revenue_vault_schema.sql")
