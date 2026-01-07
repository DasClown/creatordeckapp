"""
REVENUE & VAULT ANALYTICS MODULE
Tracking für Umsatz und Medien-Performance
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def process_of_csv(uploaded_file, user_email):
    """
    Verarbeitet OnlyFans CSV-Export und importiert Revenue-Daten.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        user_email: User Email
    
    Returns:
        int: Anzahl importierter Einträge
    """
    try:
        df = pd.read_csv(uploaded_file)
        
        # OnlyFans CSV-Struktur Mapping
        entries = []
        for _, row in df.iterrows():
            # Brutto-Berechnung (falls nur Netto vorhanden)
            amount_net = float(row.get('Amount', 0))
            fee_percentage = 20.0
            amount_gross = amount_net / (1 - fee_percentage / 100) if amount_net > 0 else 0
            
            entries.append({
                "user_id": user_email,
                "platform": "onlyfans",
                "amount_net": amount_net,
                "amount_gross": amount_gross,
                "fee_percentage": fee_percentage,
                "source": row.get('Type', 'unknown').lower(),
                "description": row.get('Description', ''),
                "created_at": row.get('Date')
            })
        
        if entries:
            from app import init_supabase
            supabase = init_supabase()
            supabase.table("revenue_history").insert(entries).execute()
            return len(entries)
    except Exception as e:
        st.error(f"CSV Processing Error: {e}")
        st.info("💡 Stelle sicher, dass die CSV die Spalten 'Amount', 'Type', 'Date' enthält.")
    return 0

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
        
        st.markdown("---")
        st.markdown("### 📤 IMPORT CSV")
        
        uploaded_file = st.file_uploader(
            "OnlyFans Revenue CSV",
            type=['csv'],
            help="Lade deine OnlyFans Revenue-Export-CSV hoch",
            key="of_csv_upload"
        )
        
        if uploaded_file is not None:
            if st.button("IMPORT CSV", use_container_width=True):
                imported_count = process_of_csv(uploaded_file, user_email)
                if imported_count > 0:
                    st.success(f"✅ {imported_count} Einträge importiert!")
                    st.rerun()
                else:
                    st.error("❌ Import fehlgeschlagen")
    
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
        
        # Whale Watcher
        st.markdown("---")
        whale_watcher(supabase)
        
        # Content Cash-Cow Scoring
        display_vault_scoring(supabase)
        
        # Whale Retention Watch
        whale_retention_check(supabase)
        
    except Exception as e:
        st.error(f"ANALYTICS ERROR: {e}")
        st.info("💡 Make sure you've run the migration: migrations/004_revenue_vault_schema.sql")

def whale_watcher(supabase):
    """
    Zeigt Top Spender basierend auf Revenue History.
    
    Aggregiert Umsatz nach Source-Feld (z.B. PPV, Tips, Subscription).
    Nützlich für schnelle Übersicht ohne dedizierte Customer-Tabelle.
    """
    st.subheader("🐋 WHALE WATCHER (TOP SPENDER)")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    try:
        # Aggregiere Umsatz pro Source
        res = supabase.table("revenue_history")\
            .select("source, amount_net, platform")\
            .eq("user_id", user_email)\
            .execute()
        
        if res.data and len(res.data) > 0:
            df = pd.DataFrame(res.data)
            
            # Top Spender nach Source
            top_spenders = df.groupby('source')['amount_net'].sum().sort_values(ascending=False).head(5)
            
            if not top_spenders.empty:
                st.markdown("**Top 5 Revenue Sources:**")
                
                # Als formatierte Tabelle
                top_df = pd.DataFrame({
                    'Source': top_spenders.index,
                    'Total Revenue ($)': top_spenders.values
                })
                top_df['Total Revenue ($)'] = top_df['Total Revenue ($)'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(
                    top_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Zusätzliche Insights
                col1, col2 = st.columns(2)
                col1.metric("TOP SOURCE", top_spenders.index[0].upper())
                col2.metric("TOP REVENUE", f"${top_spenders.values[0]:,.2f}")
            else:
                st.info("Keine Spender-Daten vorhanden")
        else:
            st.info("💡 Noch keine Revenue-Daten. Logge Transaktionen in der Sidebar.")
            
    except Exception as e:
        st.error(f"Whale Watcher Error: {e}")

def display_vault_scoring(supabase):
    """
    Content Cash-Cow Scoring System.
    
    Analysiert Top-Performing-Content und gibt strategische Empfehlungen
    basierend auf Conversion-Rate und Revenue-Effizienz.
    """
    st.divider()
    st.subheader("🔥 CONTENT CASH-COW SCORING")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    try:
        # Top-Performing-Content aus View abrufen
        res = supabase.table("top_performing_content")\
            .select("*")\
            .eq("user_id", user_email)\
            .limit(10)\
            .execute()
        
        if res.data and len(res.data) > 0:
            st.info("💡 **Scoring-Logik:** Conversion Rate × 10 (max 100). Höherer Score = bessere Performance.")
            
            for item in res.data:
                # Score berechnen (normiert auf 100)
                conversion_rate = float(item.get('conversion_rate', 0))
                score = min(int(conversion_rate * 10), 100)
                
                # Rank und Asset-Name
                rank = int(item.get('efficiency_rank', 0))
                asset_name = item.get('asset_name', 'Unknown')
                
                with st.expander(f"🏆 RANK #{rank} - {asset_name}"):
                    col1, col2, col3 = st.columns(3)
                    
                    # Metriken
                    col1.metric("Score", f"{score}/100")
                    col2.metric("Revenue", f"${float(item.get('total_revenue', 0)):,.2f}")
                    col3.metric("Efficiency", f"${conversion_rate:.2f}/View")
                    
                    # Zusätzliche Metriken
                    st.markdown("---")
                    col4, col5, col6 = st.columns(3)
                    col4.metric("PPV Opens", f"{int(item.get('ppv_opens', 0)):,}")
                    col5.metric("Likes", f"{int(item.get('likes', 0)):,}")
                    col6.metric("Platform", item.get('platform', 'unknown').upper())
                    
                    # Strategische Empfehlungen
                    st.markdown("---")
                    st.markdown("**🎯 STRATEGISCHE EMPFEHLUNG:**")
                    
                    if score >= 80:
                        st.success("""
                        **CASH-COW DETECTED!** 🐄💰
                        - Sofort als PPV-Wiederholung promoten
                        - Cross-Platform auf Fansly/OnlyFans teilen
                        - Ähnlichen Content produzieren
                        - In Premium-Bundles packen
                        """)
                    elif score >= 50:
                        st.info("""
                        **SOLID PERFORMER** ✅
                        - Für Standard-PPV geeignet
                        - Gelegentlich re-promoten
                        - Als Filler-Content nutzen
                        """)
                    elif score >= 20:
                        st.warning("""
                        **UNDERPERFORMER** ⚠️
                        - Nur als Free-Teaser nutzen
                        - Nicht mehr für Paid-Promotion
                        - Analyse: Warum niedrige Performance?
                        """)
                    else:
                        st.error("""
                        **CONTENT-BURNOUT** 🗑️
                        - NICHT mehr für Paid-Promotion nutzen
                        - Eventuell komplett archivieren
                        - Learnings für zukünftigen Content
                        """)
            
        else:
            st.info("💡 Noch nicht genügend Daten für das Scoring vorhanden.")
            st.markdown("""
            **So sammelst du Daten:**
            1. Füge Assets in der Vault hinzu
            2. Logge Revenue und PPV-Opens
            3. System berechnet automatisch Scores
            """)
            
    except Exception as e:
        st.error(f"Content Scoring Error: {e}")
        st.info("💡 Stelle sicher, dass Migration 007 ausgeführt wurde: `migrations/007_content_scoring.sql`")

def whale_retention_check(supabase):
    """
    Whale Retention Watch - Überwacht Top-Spender-Aktivität.
    
    Zeigt die letzten Transaktionen der Top-Spender und warnt bei Inaktivität.
    Hilft bei proaktiver Retention-Strategie.
    """
    st.divider()
    st.subheader("🐋 WHALE RETENTION WATCH")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    try:
        # Top Spender nach Gesamtumsatz
        whales = supabase.table("revenue_history")\
            .select("source, amount_net, created_at, platform")\
            .eq("user_id", user_email)\
            .order("amount_net", desc=True)\
            .limit(10)\
            .execute()
        
        if whales.data and len(whales.data) > 0:
            df_whales = pd.DataFrame(whales.data)
            
            # Datum formatieren
            df_whales['created_at'] = pd.to_datetime(df_whales['created_at'])
            df_whales['days_ago'] = (datetime.now() - df_whales['created_at']).dt.days
            
            # Formatierung für Display
            df_display = df_whales.copy()
            df_display['created_at'] = df_display['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            df_display['amount_net'] = df_display['amount_net'].apply(lambda x: f"${x:,.2f}")
            
            # Inaktivitäts-Warnung
            inactive_whales = df_whales[df_whales['days_ago'] > 5]
            
            if not inactive_whales.empty:
                st.warning(f"⚠️ **{len(inactive_whales)} Whale(s) inaktiv seit >5 Tagen!**")
                st.info("💡 **Retention-Strategie:** Sende personalisierte Nachrichten, exklusive Previews oder Special-Offers.")
            else:
                st.success("✅ Alle Top-Spender sind aktiv!")
            
            # Tabelle
            st.markdown("**Top 10 Recent Whale Transactions:**")
            st.dataframe(
                df_display[['source', 'amount_net', 'platform', 'created_at', 'days_ago']],
                use_container_width=True,
                hide_index=True
            )
            
            # Retention-Tipps
            with st.expander("📚 RETENTION-STRATEGIEN"):
                st.markdown("""
                **Für Whales mit >5 Tagen Inaktivität:**
                
                1. **Personalisierte DM:**
                   - "Hey [Name], vermisse dich! Hier ist ein exklusiver Preview..."
                   - Zeige Wertschätzung für ihre Unterstützung
                
                2. **Exklusive Angebote:**
                   - Special-Discount auf Premium-Content
                   - Early-Access zu neuem Content
                   - Custom-Content-Anfragen
                
                3. **Re-Engagement-Content:**
                   - Teaser von neuem Material
                   - Behind-the-Scenes
                   - "Miss you" Posts
                
                4. **Loyalty-Rewards:**
                   - VIP-Status
                   - Bonus-Content
                   - Shoutouts
                """)
        else:
            st.info("💡 Noch keine Whale-Transaktionen vorhanden.")
            
    except Exception as e:
        st.error(f"Whale Retention Error: {e}")
