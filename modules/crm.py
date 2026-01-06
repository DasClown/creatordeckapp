import streamlit as st
import pandas as pd
from supabase import create_client

def render_crm(supabase):
    st.title("CRM")
    
    # Deals aus DB laden
    try:
        res = supabase.table("deals").select("*").execute()
        
        if not res.data:
            st.info("Keine Deals gefunden. Starte eine neue Verhandlung!")
            # Create an empty DataFrame with flexible columns
            df_deals = pd.DataFrame(columns=["brand", "status", "value", "deadline"])
        else:
            df_deals = pd.DataFrame(res.data)
            
            # Spalten-Mapping: Unterstütze beide Schemas
            # Altes Schema: brand, status, value, deadline
            # Neues Schema: brand, stage, value, date
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
        edited_df = st.data_editor(
            df_deals[["brand", "status", "value", "deadline"]], 
            width="stretch", 
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
                        # Wert als Float konvertieren (entfernt € und Kommas)
                        try:
                            value_str = str(row.get("value", "0"))
                            amount = float(value_str.replace("€", "").replace(".", "").replace(",", ".").strip())
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
            brand TEXT,
            status TEXT DEFAULT 'Negotiating',
            value TEXT,
            deadline TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        ALTER TABLE deals DISABLE ROW LEVEL SECURITY;
        ```
        """)
