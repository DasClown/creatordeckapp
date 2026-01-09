import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def render_finance(supabase):
    st.title("FINANCE")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    # Auto-Sync from Revenue History
    st.info("💡 Finance data is automatically synced from Revenue History. No manual entry needed!")
    
    col_refresh, col_spacer = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 REFRESH DATA", use_container_width=True):
            st.rerun()
    
    # Daten aus revenue_history laden und zu transactions konvertieren
    try:
        rev_res = supabase.table("revenue_history")\
            .select("*")\
            .eq("user_id", user_email)\
            .execute()
        
        if rev_res.data and len(rev_res.data) > 0:
            # Konvertiere revenue_history zu transaction format
            transactions = []
            for item in rev_res.data:
                transactions.append({
                    "date": item.get('created_at', datetime.now().isoformat())[:10],
                    "type": "Income",
                    "amount": float(item.get('amount_net', 0)),
                    "category": item.get('source', 'unknown').title(),
                    "description": f"{item.get('platform', 'unknown').title()} - {item.get('source', 'revenue')}"
                })
            
            df = pd.DataFrame(transactions)
            df["amount"] = df["amount"].astype(float)
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Forecast-Berechnung
            today = datetime.now().date()
            
            actual_revenue = df[(df['type'] == 'Income') & (df['date'] <= today)]['amount'].sum()
            forecast_revenue = df[(df['type'] == 'Income') & (df['date'] > today)]['amount'].sum()
            
            # Expenses aus transactions table (falls vorhanden)
            try:
                exp_res = supabase.table("transactions")\
                    .select("amount")\
                    .eq("type", "Expense")\
                    .execute()
                burn_rate = sum(float(e.get('amount', 0)) for e in exp_res.data) if exp_res.data else 0
            except:
                burn_rate = 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Current Cash", f"${actual_revenue:,.2f}")
            col2.metric("Pipeline Forecast", f"${forecast_revenue:,.2f}", delta="+ Deals")
            col3.metric("Burn Rate", f"${burn_rate:,.2f}", delta_color="inverse")

            # Visualisierung des Cashflow-Verlaufs
            st.subheader("Cashflow Projection")
            fig = px.line(df.sort_values("date"), x="date", y="amount", color="type", template="plotly_white")
            fig.update_traces(
                line_color="#000000", 
                fillcolor="rgba(0,0,0,0.02)",
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

            # Transaction Log (Read-Only)
            st.subheader("Transaction Log (Auto-Synced)")
            st.caption("💡 Data is automatically synced from Revenue History. To add transactions, use the Revenue Vault module.")
            
            # Sortiere nach Datum (neueste zuerst)
            df_display = df.sort_values('date', ascending=False)
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No revenue data yet. Use the Revenue Vault module to log your first transaction!")
            
    except Exception as e:
        st.error(f"Finance Error: {e}")
        st.info("💡 Make sure you have revenue data in the Revenue Vault module.")
