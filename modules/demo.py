import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def render_demo():
    st.title("🧪 SANDBOX / DEMO")
    st.info("Hier können neue Features getestet werden, ohne die Live-Daten zu beeinflussen.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("UI Components")
        st.slider("Metric Simulation", 0, 100, 50)
        st.multiselect("Feature Test", ["AI Logic", "Direct API", "Custom CSS"], ["AI Logic"])
        st.button("Trigger Test Notification")

    with col2:
        st.subheader("Live Chart Simulation")
        chart_data = pd.DataFrame(
            np.random.randn(20, 3),
            columns=['Followers', 'Reach', 'Engagement']
        )
        st.line_chart(chart_data)

    st.divider()
    st.subheader("API JSON Preview")
    demo_json = {
        "status": "connected",
        "api_endpoint": "https://api.creator.tech/v1/test",
        "mock_data": True,
        "latency": "45ms"
    }
    st.json(demo_json)
