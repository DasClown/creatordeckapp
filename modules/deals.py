import streamlit as st
import pandas as pd

def render_deals():
    st.title("🤝 DEAL FLOW")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pipeline Value", "24.500 €")
    col2.metric("Signed This Month", "3")
    col3.metric("Avg. Deal Size", "4.100 €")

    st.subheader("Active Negotiations")
    # Status-basiertes Board
    deals = pd.DataFrame([
        {"Brand": "Samsung", "Stage": "Drafting", "Value": "8.000 €", "Date": "2026-02-15"},
        {"Brand": "Lululemon", "Stage": "Sent", "Value": "3.500 €", "Date": "2026-01-20"},
        {"Brand": "Tesla", "Stage": "Negotiating", "Value": "12.000 €", "Date": "2026-03-01"}
    ])
    
    st.data_editor(deals, use_container_width=True, num_rows="dynamic")
    
    if st.button("➕ CREATE NEW DEAL"):
        st.toast("Deal Template created.")
