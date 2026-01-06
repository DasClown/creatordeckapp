import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import uuid

def render_planner(supabase):
    st.title("CONTENT PLANNER")
    
    # Zwei-Spalten Layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 Neuen Post planen")
        
        with st.form("new_post_form", clear_on_submit=True):
            # Basis-Felder
            publish_date = st.date_input("Veröffentlichungsdatum", datetime.now())
            platform = st.selectbox("Platform", ["Instagram", "TikTok", "YouTube", "LinkedIn"])
            content_type = st.selectbox("Content-Typ", ["Reel", "Post", "Story", "Video", "Carousel"])
            
            # Optionale Felder
            title = st.text_input("Titel / Hook")
            caption = st.text_area("Caption", height=100, placeholder="Deine Caption für den Post...")
            
            # Bild-Upload
            uploaded_image = st.file_uploader("Bild / Thumbnail", type=["jpg", "png", "jpeg"])
            
            # Submit
            submit = st.form_submit_button("📅 POST PLANEN", use_container_width=True)
            
            if submit:
                # Bild zu Supabase Storage hochladen (falls vorhanden)
                asset_url = None
                if uploaded_image:
                    try:
                        img = Image.open(uploaded_image)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        
                        file_path = f"content_plan/{uuid.uuid4()}.png"
                        supabase.storage.from_("assets").upload(file_path, buf.getvalue())
                        asset_url = supabase.storage.from_("assets").get_public_url(file_path)
                    except Exception as e:
                        st.warning(f"Bild-Upload fehlgeschlagen: {str(e)}")
                
                # Post speichern - versuche verschiedene Schema-Varianten
                saved = False
                error_msg = None
                
                # Variante 1: Versuche mit c_type (existierendes Schema) - NUR Pflichtfelder
                try:
                    post_data = {
                        "publish_date": str(publish_date),
                        "platform": platform,
                        "c_type": content_type
                    }
                    # Keine optionalen Felder - die Tabelle hat sie nicht!
                    
                    supabase.table("content_plan").insert(post_data).execute()
                    saved = True
                    st.success("✅ Post geplant!")
                    
                    # Warnung wenn Felder nicht gespeichert werden konnten
                    if title or caption or asset_url:
                        st.info("ℹ️ Titel, Caption und Bild werden nicht gespeichert (Spalten fehlen in Tabelle)")
                    
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                
                # Variante 2: Falls c_type fehlschlägt, versuche content_type
                if not saved:
                    try:
                        post_data = {
                            "publish_date": str(publish_date),
                            "platform": platform,
                            "content_type": content_type
                        }
                        if title:
                            post_data["title"] = title
                        if caption:
                            post_data["caption"] = caption
                        if asset_url:
                            post_data["asset_url"] = asset_url
                        
                        supabase.table("content_plan").insert(post_data).execute()
                        saved = True
                        st.success("✅ Post geplant!")
                        st.rerun()
                    except Exception as e2:
                        error_msg = str(e2)
                
                # Wenn beide fehlschlagen, zeige Fehler
                if not saved:
                    st.error(f"Fehler beim Speichern: {error_msg}")
                    st.info("""
                    **Tabelle fehlt oder hat falsches Schema.**
                    
                    Erstelle sie mit:
                    ```sql
                    CREATE TABLE IF NOT EXISTS content_plan (
                        id SERIAL PRIMARY KEY,
                        publish_date TEXT,
                        platform TEXT,
                        c_type TEXT,
                        title TEXT,
                        caption TEXT,
                        asset_url TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                    ALTER TABLE content_plan DISABLE ROW LEVEL SECURITY;
                    ```
                    """)
    
    with col2:
        st.subheader("📅 Geplante Posts")
        
        # Filter
        filter_platform = st.selectbox("Filter Platform", ["Alle", "Instagram", "TikTok", "YouTube", "LinkedIn"], key="filter_platform")
        
        # Posts laden
        try:
            res = supabase.table("content_plan").select("*").order("publish_date", desc=False).execute()
            
            if res.data:
                posts = res.data
                
                # Spalten-Mapping für Anzeige
                for post in posts:
                    if 'c_type' in post:
                        post['content_type'] = post['c_type']
                
                # Filter
                if filter_platform != "Alle":
                    posts = [p for p in posts if p.get("platform") == filter_platform]
                
                # Posts als Cards
                for post in posts:
                    with st.container():
                        st.markdown("---")
                        
                        # Header
                        post_col1, post_col2 = st.columns([3, 1])
                        with post_col1:
                            st.markdown(f"**{post.get('title', post.get('content_type', 'Post'))}**")
                        with post_col2:
                            st.caption(f"📅 {post.get('publish_date', 'N/A')}")
                        
                        # Content
                        content_col1, content_col2 = st.columns([1, 2])
                        
                        with content_col1:
                            if post.get('asset_url'):
                                st.image(post['asset_url'], width=150)
                            else:
                                st.info("Kein Bild")
                        
                        with content_col2:
                            st.caption(f"**Platform:** {post.get('platform', 'N/A')} | **Typ:** {post.get('content_type', 'N/A')}")
                            
                            # Caption
                            caption = post.get('caption', '')
                            if caption:
                                if len(caption) > 150:
                                    st.text(caption[:150] + "...")
                                else:
                                    st.text(caption)
                            
                            # Delete
                            if st.button("🗑️ Löschen", key=f"delete_{post['id']}"):
                                supabase.table("content_plan").delete().eq("id", post['id']).execute()
                                st.rerun()
            else:
                st.info("📭 Noch keine Posts geplant. Erstelle deinen ersten Post links!")
                
        except Exception as e:
            st.error(f"Fehler beim Laden: {str(e)}")
            st.info("Prüfe ob die 'content_plan' Tabelle in Supabase existiert.")
