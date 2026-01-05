import streamlit as st
import pandas as pd
import plotly.express as px

def render_finance(supabase):
    st.title("💰 FINANCE CONTROL")

    # Daten laden
    res = supabase.table("transactions").select("*").order("date").execute()
    df = pd.DataFrame(res.data)

    if df.empty:
        st.info("Keine Transaktionen gefunden.")
        df = pd.DataFrame(columns=["date", "type", "amount", "category", "description"])
    else:
        df["amount"] = df["amount"].astype(float)

    # Metriken berechnen
    inc = df[df["type"] == "Income"]["amount"].sum()
    exp = df[df["type"] == "Expense"]["amount"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"{inc:,.2f} €")
    c2.metric("Total Expenses", f"{exp:,.2f} €", delta_color="inverse")
    c3.metric("Net Profit", f"{(inc - exp):,.2f} €")

    # Editor für neue Einträge
    st.subheader("Transaction Log")
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)

    if st.button("SYNC TRANSACTIONS"):
        # Bulk Sync Logik (vereinfacht: löschen und neu schreiben oder Upsert)
        for _, row in edited_df.iterrows():
            data = {k: v for k, v in row.items() if pd.notnull(v) and k != 'id'}
            if "id" in row and pd.notnull(row["id"]):
                supabase.table("transactions").update(data).eq("id", row["id"]).execute()
            else:
                supabase.table("transactions").insert(data).execute()
        st.success("Finance Data Synced.")
