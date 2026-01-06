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
            # Create an empty DataFrame with the expected columns for the editor
            df_deals = pd.DataFrame(columns=["brand", "stage", "value", "date"])
        else:
            df_deals = pd.DataFrame(res.data)
        
        # Prüfe ob erforderliche Spalten existieren
        required_columns = ["brand", "stage", "value", "date"]
        missing_columns = [col for col in required_columns if col not in df_deals.columns]
        
        if missing_columns:
            st.error(f"🗂️ **DATENBANK-SCHEMA FEHLER**")
            st.warning(f"""
            Die 'deals' Tabelle fehlt folgende Spalten: {', '.join(missing_columns)}
            
            **Erforderliche Spalten:**
            - brand (text)
            - stage (text)
            - value (text oder numeric)
            - date (date oder text)
            
            **Lösung:**
            1. Gehe zu Supabase Dashboard
            2. SQL Editor → Neue Query
            3. Erstelle Tabelle mit korrektem Schema:
            
            ```sql
            CREATE TABLE IF NOT EXISTS deals (
                id SERIAL PRIMARY KEY,
                brand TEXT,
                stage TEXT,
                value TEXT,
                date TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            ```
            
            **Alternative:** CRM-Feature vorübergehend nicht nutzen
            """)
            return
    except Exception as e:
        st.error(f"CRM Datenbankfehler: {str(e)}")
        st.info("Tipp: Prüfe ob 'deals' Tabelle in Supabase existiert")
        return

    # UI
    st.subheader("Active Pipeline")
    edited_df = st.data_editor(df_deals, width="stretch", hide_index=True, num_rows="dynamic")
    
    if st.button("SAVE CHANGES"):
        # Logik zum Updaten/Einfügen in Supabase
        for index, row in edited_df.iterrows():
            deal_data = {
                "brand": row["brand"],
                "status": row["status"],
                "value": row["value"],
                "deadline": row["deadline"]
            }
            if "id" in row and pd.notnull(row["id"]):
                supabase.table("deals").update(deal_data).eq("id", row["id"]).execute()
            else:
                supabase.table("deals").insert(deal_data).execute()
            
            # Automatischer Finance-Sync für geschlossene Deals
            if row["status"] == "Closed":
                # Prüfen, ob bereits eine Transaktion für diesen Deal existiert (Double-Entry Schutz)
                check = supabase.table("transactions").select("id").eq("description", f"Deal: {row['brand']}").execute()
                
                if not check.data:
                    # Wert als Float konvertieren (entfernt € und Kommas)
                    try:
                        amount = float(str(row["value"]).replace("€", "").replace(".", "").replace(",", ".").strip())
                    except:
                        amount = 0
                    
                    supabase.table("transactions").insert({
                        "type": "Income",
                        "amount": amount,
                        "category": "Brand Deal",
                        "description": f"Deal: {row['brand']}",
                        "date": str(row["deadline"])
                    }).execute()
                    st.toast(f"Finance: {row['brand']} als Einnahme verbucht!")
        
        st.success("Daten synchronisiert.")

