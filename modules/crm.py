import streamlit as st
import pandas as pd
from supabase import create_client

def render_crm(supabase):
    st.title("CRM")
    
    # Daten aus Supabase laden
    response = supabase.table("deals").select("*").execute()
    df_deals = pd.DataFrame(response.data)

    if df_deals.empty:
        st.info("Keine Deals gefunden. Starte eine neue Verhandlung!")
        df_deals = pd.DataFrame(columns=["brand", "status", "value", "deadline"])

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

