import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def render_finance(supabase):
    st.title("💰 FINANCE CONTROL")
    
    # Daten laden
    res = supabase.table("transactions").select("*").execute()
    df = pd.DataFrame(res.data)
    
    if df.empty:
        st.info("Keine Transaktionen gefunden.")
        df = pd.DataFrame(columns=["date", "type", "amount", "category", "description"])
    else:
        df["amount"] = df["amount"].astype(float)
        
        # Forecast-Berechnung: Deals, die 'Closed' aber in der Zukunft liegen
        today = datetime.now().date()
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        actual_revenue = df[(df['type'] == 'Income') & (df['date'] <= today)]['amount'].sum()
        forecast_revenue = df[(df['type'] == 'Income') & (df['date'] > today)]['amount'].sum()
        burn_rate = df[df['type'] == 'Expense']['amount'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Cash", f"{actual_revenue:,.2f} €")
        col2.metric("Pipeline Forecast", f"{forecast_revenue:,.2f} €", delta="+ Deals")
        col3.metric("Burn Rate", f"{burn_rate:,.2f} €", delta_color="inverse")

        # Visualisierung des Cashflow-Verlaufs
        st.subheader("Cashflow Projection")
        fig = px.line(df.sort_values("date"), x="date", y="amount", color="type", template="plotly_white")
        fig.update_traces(
            line_color="#000000", 
            fillcolor="rgba(0,0,0,0.02)",  # Hauch von Grau
            line_width=1.5
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_showgrid=False,
            yaxis_showgrid=True,
            yaxis_gridcolor="#F0F0F0",
            font_color="#000000"
        )
        st.plotly_chart(fig, use_container_width=True)

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
