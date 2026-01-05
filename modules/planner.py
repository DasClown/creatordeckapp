import streamlit as st
import pandas as pd

def render_planner():
    st.title("📅 CONTENT PLANNER")
    
    # Einfache Kalender-Simulaton
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    
    for i, day in enumerate(days):
        with cols[i]:
            st.markdown(f"**{day}**")
            if i % 2 == 0:
                st.caption("🎬 Reel: AI Tools")
            else:
                st.caption("📸 Photo: Lifestyle")

    st.divider()
    st.subheader("Backlog & Ideas")
    ideas = ["Setup Tour", "Q&A Session", "Day in the Life", "Software Review"]
    for idea in ideas:
        st.checkbox(idea)
