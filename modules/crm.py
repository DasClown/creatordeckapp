import streamlit as st
import pandas as pd
from supabase import create_client

def sync_customers_to_crm(supabase, user_email):
    """
    Synchronisiert Kunden aus OnlyFans/Fansly in CRM.
    Erstellt automatisch Deals für High-Value Customers (Whales).
    
    Returns:
        tuple: (customers_synced, deals_created)
    """
    customers_synced = 0
    deals_created = 0
    
    try:
        # 1. Hole Top Spender aus revenue_history
        rev_res = supabase.table("revenue_history")\
            .select("source, amount_net, platform")\
            .eq("user_id", user_email)\
            .execute()
        
        if rev_res.data and len(rev_res.data) > 0:
            df = pd.DataFrame(rev_res.data)
            
            # Aggregiere nach Source (Customer Identifier)
            customer_spending = df.groupby(['source', 'platform'])['amount_net'].sum().reset_index()
            customer_spending = customer_spending.sort_values('amount_net', ascending=False)
            
            # Erstelle Deals für Kunden mit >$50 Umsatz
            for _, row in customer_spending.iterrows():
                if row['amount_net'] >= 50:  # Whale threshold
                    customer_name = row['source'].title()
                    platform = row['platform'].title()
                    total_value = row['amount_net']
                    
                    # Prüfe ob Deal bereits existiert
                    existing = supabase.table("deals")\
                        .select("id")\
                        .eq("brand", f"{customer_name} ({platform})")\
                        .execute()
                    
                    if not existing.data:
                        # Erstelle neuen Deal
                        deal_data = {
                            "brand": f"{customer_name} ({platform})",
                            "status": "Active" if total_value >= 100 else "Negotiating",
                            "value": f"${total_value:.2f}",
                            "deadline": "",
                            "user_id": user_email
                        }
                        
                        supabase.table("deals").insert(deal_data).execute()
                        deals_created += 1
                        customers_synced += 1
        
        # 2. Hole OnlyFans Customers (falls Tabelle existiert)
        try:
            of_customers = supabase.table("onlyfans_customers")\
                .select("*")\
                .eq("user_id", user_email)\
                .execute()
            
            if of_customers.data:
                for customer in of_customers.data:
                    customer_name = customer.get('username', 'Unknown')
                    total_spent = float(customer.get('total_spent', 0))
                    
                    if total_spent >= 50:
                        # Prüfe ob Deal existiert
                        existing = supabase.table("deals")\
                            .select("id")\
                            .eq("brand", f"{customer_name} (OnlyFans)")\
                            .execute()
                        
                        if not existing.data:
                            deal_data = {
                                "brand": f"{customer_name} (OnlyFans)",
                                "status": "Active" if total_spent >= 100 else "Negotiating",
                                "value": f"${total_spent:.2f}",
                                "deadline": "",
                                "user_id": user_email
                            }
                            
                            supabase.table("deals").insert(deal_data).execute()
                            deals_created += 1
                            customers_synced += 1
        except:
            pass  # Tabelle existiert nicht
        
        return (customers_synced, deals_created)
        
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return (0, 0)

def render_crm(supabase):
    st.title("CRM")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    # Auto-Sync Button
    st.info("💡 CRM can automatically sync customers from your revenue data!")
    
    col_sync, col_spacer = st.columns([1, 3])
    with col_sync:
        if st.button("🔄 AUTO-SYNC CUSTOMERS", use_container_width=True):
            with st.spinner("Syncing customers..."):
                customers, deals = sync_customers_to_crm(supabase, user_email)
                if customers > 0 or deals > 0:
                    st.success(f"✅ Synced {customers} customers, created {deals} new deals!")
                    st.rerun()
                else:
                    st.info("No new customers to sync. Make sure you have revenue data in Revenue Vault.")
    
    st.markdown("---")
    
    # Deals aus DB laden
    try:
        res = supabase.table("deals").select("*").eq("user_id", user_email).execute()
        
        if not res.data:
            st.info("No deals found. Click 'AUTO-SYNC CUSTOMERS' to import from your revenue data!")
            # Create an empty DataFrame with flexible columns
            df_deals = pd.DataFrame(columns=["brand", "status", "value", "deadline"])
        else:
            df_deals = pd.DataFrame(res.data)
            
            # Spalten-Mapping: Unterstütze beide Schemas
            if 'stage' in df_deals.columns and 'status' not in df_deals.columns:
                df_deals.rename(columns={'stage': 'status'}, inplace=True)
            if 'date' in df_deals.columns and 'deadline' not in df_deals.columns:
                df_deals.rename(columns={'date': 'deadline'}, inplace=True)
            
            # Stelle sicher dass alle erforderlichen Spalten existieren
            required_cols = ["brand", "status", "value", "deadline"]
            for col in required_cols:
                if col not in df_deals.columns:
                    df_deals[col] = ""
        
        # UI
        st.subheader("Active Pipeline")
        st.caption(f"📊 {len(df_deals)} deals in pipeline")
        
        edited_df = st.data_editor(
            df_deals[["brand", "status", "value", "deadline"]], 
            use_container_width=True,
            hide_index=True, 
            num_rows="dynamic"
        )
        
        if st.button("SAVE CHANGES"):
            # Logik zum Updaten/Einfügen in Supabase
            for index, row in edited_df.iterrows():
                # Skip leere Zeilen
                if not row.get("brand"):
                    continue
                    
                deal_data = {
                    "user_id": user_email,
                    "brand": str(row.get("brand", "")),
                    "status": str(row.get("status", "Negotiating")),
                    "value": str(row.get("value", "")),
                    "deadline": str(row.get("deadline", ""))
                }
                
                # Prüfe ob Deal bereits existiert (hat ID)
                if index < len(res.data) and "id" in res.data[index]:
                    # Update existierender Deal
                    deal_id = res.data[index]["id"]
                    supabase.table("deals").update(deal_data).eq("id", deal_id).execute()
                else:
                    # Neuer Deal
                    supabase.table("deals").insert(deal_data).execute()
                
                # Automatischer Finance-Sync für geschlossene Deals
                if row.get("status") == "Closed":
                    # Prüfen, ob bereits eine Transaktion für diesen Deal existiert
                    check = supabase.table("transactions").select("id").eq("description", f"Deal: {row['brand']}").execute()
                    
                    if not check.data:
                        # Wert als Float konvertieren (entfernt $ und Kommas)
                        try:
                            value_str = str(row.get("value", "0"))
                            amount = float(value_str.replace("$", "").replace("€", "").replace(".", "").replace(",", ".").strip())
                        except:
                            amount = 0
                        
                        if amount > 0:
                            supabase.table("transactions").insert({
                                "type": "Income",
                                "amount": amount,
                                "category": "Brand Deal",
                                "description": f"Deal: {row['brand']}",
                                "date": str(row.get("deadline", ""))
                            }).execute()
                            st.toast(f"Finance: {row['brand']} als Einnahme verbucht!")
            
            st.success("Daten synchronisiert.")
            st.rerun()
            
    except Exception as e:
        st.error(f"CRM Fehler: {str(e)}")
        st.info("""
        **Tipp:** Erstelle die 'deals' Tabelle in Supabase:
        
        ```sql
        CREATE TABLE IF NOT EXISTS deals (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            brand TEXT,
            status TEXT DEFAULT 'Negotiating',
            value TEXT,
            deadline TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        ALTER TABLE deals DISABLE ROW LEVEL SECURITY;
        ```
        """)
