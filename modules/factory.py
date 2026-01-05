import streamlit as st
import pandas as pd
import google.generativeai as genai

def render_factory(supabase):
    st.title("FACTORY")
    
    # Echtzeit-Daten aus der neuen Historie abrufen
    try:
        res = supabase.table("stats_history").select("*").order("value", desc=True).limit(5).execute()
        top_data = pd.DataFrame(res.data)
    except:
        top_data = pd.DataFrame()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("STRATEGY INPUT")
        topic = st.text_area("Thema", placeholder="Worüber willst du posten?")
        vibe = st.select_slider("Vibe", options=["Deep", "Direct", "Hype", "Value"])
        
        if st.button("GENERATE CONTENT ⚡"):
            if topic:
                with st.spinner("AI analysiert Top-Performance..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Kontext-Vorbereitung aus DB
                    context = top_data.to_string() if not top_data.empty else "Keine Historiendaten vorhanden."
                    
                    prompt = f"""
                    Rolle: Content-Stratege für Creator.
                    Thema: {topic}
                    Vibe: {vibe}
                    Performance-Kontext: {context}
                    
                    Aufgabe:
                    1. Starker Hook (Scroll-Stopper).
                    2. Kurze, prägnante Caption (Metric System nutzen).
                    3. Visual-Idee für Reel/Foto.
                    4. CTA basierend auf aktuellem Vibe.
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.factory_output = response.text
            else:
                st.warning("Eingabe erforderlich.")

    with col2:
        st.subheader("DRAFT")
        if "factory_output" in st.session_state:
            st.markdown(f"<div class='ai-box'>{st.session_state.factory_output}</div>", unsafe_allow_html=True)
