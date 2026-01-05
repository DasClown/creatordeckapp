import streamlit as st
import pandas as pd
import google.generativeai as genai

def render_factory(df_history):
    st.title("🏭 CONTENT FACTORY")
    st.markdown("Generiere neue Post-Ideen basierend auf deiner Performance-Historie.")

    if df_history.empty:
        st.warning("Keine historischen Daten gefunden. Bitte erst ein Snapshot im Dashboard erstellen.")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Input")
        topic = st.text_area("Thema oder Stichpunkte für den nächsten Post", 
                             placeholder="z.B. 3 Tipps für produktiveres Arbeiten im Homeoffice...")
        
        target_vibe = st.selectbox("Vibe", ["Inspirierend", "Provokant", "Lehrreich", "Minimalistisch"])
        
        if st.button("GENERATE STRATEGY ⚡"):
            if topic:
                with st.spinner("AI analysiert Stil und generiert Entwurf..."):
                    # Kontext-Vorbereitung
                    top_performance = df_history.sort_values(by='Engagement', ascending=False).head(3)
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    Handle als erfahrener Social Media Stratege. 
                    Thema: {topic}
                    Vibe: {target_vibe}
                    
                    Historischer Kontext (meine besten Posts):
                    {top_performance[['Caption', 'Engagement']].to_string()}
                    
                    Erstelle:
                    1. Einen Hook (erster Satz), der zum Scroll-Stopp zwingt.
                    2. Eine Caption im Stil meiner erfolgreichsten Posts.
                    3. Visuelle Idee (Bildaufbau oder Reel-Schnitt).
                    4. Strategische Begründung, warum dieser Post funktionieren wird.
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state.factory_output = response.text
            else:
                st.error("Bitte gib ein Thema ein.")

    with col2:
        st.subheader("Draft Output")
        if "factory_output" in st.session_state:
            st.markdown(f"""
                <div class='ai-box' style='color: #1a1a1a; border-left: 4px solid #000000;'>
                    {st.session_state.factory_output}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Warte auf Input...")
