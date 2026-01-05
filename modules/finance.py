import streamlit as st
import pandas as pd
import plotly.express as px

def render_finance():
    st.title("💰 FINANCE CONTROL")
    
    col1, col2, col3 = st.columns(3)
    # Delta-Farben werden nun durch das CSS automatisch korrekt gefärbt
    col1.metric("Revenue (MTD)", "4.200 €", "+12%") 
    col2.metric("Expenses (MTD)", "850 €", "-5%", delta_color="inverse") 
    col3.metric("Net Profit", "3.350 €", "+18%")
    
    st.subheader("Cashflow History")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Chart Update für White Design
        data = pd.DataFrame({
            "Month": ["Oct", "Nov", "Dec", "Jan"],
            "Revenue": [3200, 3800, 5100, 4200]
        })
        
        fig = px.area(data, x="Month", y="Revenue", template="plotly_white")
        fig.update_traces(
            line_color="#1a1a1a", 
            fillcolor="rgba(0,0,0,0.03)",
            line_width=2
        )
        fig.update_layout(
            xaxis_showgrid=False,
            yaxis_showgrid=True,
            yaxis_gridcolor="#eeeeee",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("Invoices")
        st.button("Generate Invoice")
