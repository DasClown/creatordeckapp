import streamlit as st
import pandas as pd

def render_crm():
    st.header("💎 CRM & Deals")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Active Pipeline")
        # Dummy Daten für die Pipeline
        deals = {
            "Partner": ["Gymshark", "Oura", "Adobe"],
            "Status": ["Negotiation", "Sent", "Closed"],
            "Value": ["€5.000", "€2.500", "€10.000"]
        }
        st.table(pd.DataFrame(deals))
        
    with col2:
        st.subheader("Quick Actions")
        st.button("➕ New Contact")
        st.button("📄 Export Invoices")
