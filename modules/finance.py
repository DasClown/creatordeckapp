import streamlit as st
import pandas as pd
import plotly.express as px

def render_finance():
    st.title("💰 FINANCE CONTROL")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue (MTD)", "4.200 €", "+12%")
    col2.metric("Expenses (MTD)", "850 €", "-5%")
    col3.metric("Net Profit", "3.350 €", "+18%")
    
    st.divider()
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Cashflow History")
        data = pd.DataFrame({
            "Month": ["Oct", "Nov", "Dec", "Jan"],
            "Revenue": [3200, 3800, 5100, 4200]
        })
        fig = px.area(data, x="Month", y="Revenue", template="plotly_white")
        fig.update_traces(line_color="#000000", fillcolor="rgba(0,0,0,0.05)")
        fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("Invoices")
        st.write("✅ #INV-2026-001 (Paid)")
        st.write("⏳ #INV-2026-002 (Pending)")
        st.button("Generate Invoice")
