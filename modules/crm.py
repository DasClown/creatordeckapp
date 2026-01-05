import streamlit as st
import pandas as pd

def render_crm():
    st.title("💎 RELATIONSHIPS (CRM)")
    
    t1, t2 = st.tabs(["DEALS PIPELINE", "CONTACTS"])
    
    with t1:
        deals = {
            "Partner": ["Gymshark", "Oura", "Adobe"],
            "Status": ["Negotiation", "Sent", "Closed"],
            "Value": ["5.000€", "2.500€", "10.000€"]
        }
        st.dataframe(pd.DataFrame(deals), use_container_width=True, hide_index=True)
        st.button("➕ NEW DEAL")
        
    with t2:
        st.info("Contacts module coming soon.")
