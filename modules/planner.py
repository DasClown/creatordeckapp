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
            # Datum & Platform
            publish_date = st.date_input("Veröffentlichungsdatum", datetime.now())
            platform = st.selectbox("Platform", ["Instagram", "TikTok", "YouTube", "LinkedIn"])
            
            # Content Details
            content_type = st.selectbox("Content-Typ", ["Reel", "Post", "Story", "Video", "Carousel"])
            title = st.text_input("Titel / Hook")
            caption = st.text_area("Caption / Beschreibung", height=100)
            
            # Hashtags
            hashtags = st.text_input("Hashtags (durch Leerzeichen getrennt)")
            
            # Bild-Upload
            uploaded_image = st.file_uploader("Bild / Thumbnail", type=["jpg", "png", "jpeg"])
            
            # Status
            status = st.selectbox("Status", ["Geplant", "In Arbeit", "Bereit", "Veröffentlicht"])
            
            # Submit
            submit = st.form_submit_button("📅 POST PLANEN", use_container_width=True)
            
            if submit:
                # Bild zu Supabase Storage hochladen (falls vorhanden)
                image_url = None
                if uploaded_image:
                    try:
                        # Bild verarbeiten
                        img = Image.open(uploaded_image)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # In Buffer speichern
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        
                        # Upload zu Supabase Storage
                        file_path = f"content_plan/{uuid.uuid4()}.png"
                        supabase.storage.from_("assets").upload(file_path, buf.getvalue())
                        image_url = supabase.storage.from_("assets").get_public_url(file_path)
                        
                    except Exception as e:
                        st.warning(f"Bild-Upload fehlgeschlagen: {str(e)}")
                
                # Post in Datenbank speichern
                try:
                    post_data = {
                        "date": str(publish_date),
                        "platform": platform,
                        "content_type": content_type,
                        "title": title,
                        "caption": caption,
                        "hashtags": hashtags,
                        "image_url": image_url,
                        "status": status,
                        "user_id": st.session_state.get('user_email', 'unknown')
                    }
                    
                    supabase.table("content_plan").insert(post_data).execute()
                    st.success("✅ Post geplant!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Fehler beim Speichern: {str(e)}")
    
    with col2:
        st.subheader("📅 Geplante Posts")
        
        # Filter
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_platform = st.selectbox("Filter Platform", ["Alle", "Instagram", "TikTok", "YouTube", "LinkedIn"], key="filter_platform")
        with filter_col2:
            filter_status = st.selectbox("Filter Status", ["Alle", "Geplant", "In Arbeit", "Bereit", "Veröffentlicht"], key="filter_status")
        
        # Posts aus DB laden
        try:
            user_id = st.session_state.get('user_email', 'unknown')
            query = supabase.table("content_plan").select("*").eq("user_id", user_id).order("date", desc=False)
            res = query.execute()
            
            if res.data:
                posts = res.data
                
                # Filter anwenden
                if filter_platform != "Alle":
                    posts = [p for p in posts if p.get("platform") == filter_platform]
                if filter_status != "Alle":
                    posts = [p for p in posts if p.get("status") == filter_status]
                
                # Posts als Cards anzeigen
                for post in posts:
                    with st.container():
                        st.markdown("---")
                        
                        # Header mit Datum und Platform
                        post_col1, post_col2, post_col3 = st.columns([2, 1, 1])
                        with post_col1:
                            st.markdown(f"**{post.get('title', 'Kein Titel')}**")
                        with post_col2:
                            st.caption(f"📅 {post.get('date', 'N/A')}")
                        with post_col3:
                            # Status Badge
                            status_emoji = {
                                "Geplant": "📝",
                                "In Arbeit": "⚙️",
                                "Bereit": "✅",
                                "Veröffentlicht": "🚀"
                            }
                            st.caption(f"{status_emoji.get(post.get('status', ''), '📝')} {post.get('status', 'N/A')}")
                        
                        # Content
                        content_col1, content_col2 = st.columns([1, 2])
                        
                        with content_col1:
                            # Bild anzeigen (falls vorhanden)
                            if post.get('image_url'):
                                st.image(post['image_url'], width=150)
                            else:
                                st.info("Kein Bild")
                        
                        with content_col2:
                            st.caption(f"**Platform:** {post.get('platform', 'N/A')} | **Typ:** {post.get('content_type', 'N/A')}")
                            
                            # Caption (gekürzt)
                            caption = post.get('caption', '')
                            if caption:
                                if len(caption) > 150:
                                    st.text(caption[:150] + "...")
                                else:
                                    st.text(caption)
                            
                            # Hashtags
                            if post.get('hashtags'):
                                st.caption(f"🏷️ {post.get('hashtags')}")
                            
                            # Actions
                            action_col1, action_col2 = st.columns(2)
                            with action_col1:
                                if st.button("🗑️ Löschen", key=f"delete_{post['id']}"):
                                    supabase.table("content_plan").delete().eq("id", post['id']).execute()
                                    st.rerun()
                            with action_col2:
                                if st.button("✏️ Bearbeiten", key=f"edit_{post['id']}"):
                                    st.info("Bearbeiten-Feature kommt bald!")
            else:
                st.info("📭 Noch keine Posts geplant. Erstelle deinen ersten Post links!")
                
        except Exception as e:
            error_msg = str(e)
            st.error("PLANNER Fehler")
            
            if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
                st.warning("""
                **Die 'content_plan' Tabelle fehlt in Supabase.**
                
                Erstelle sie mit dieser SQL-Query:
                
                ```sql
                CREATE TABLE IF NOT EXISTS content_plan (
                    id SERIAL PRIMARY KEY,
                    date TEXT,
                    platform TEXT DEFAULT 'Instagram',
                    content_type TEXT DEFAULT 'Post',
                    title TEXT,
                    caption TEXT,
                    hashtags TEXT,
                    image_url TEXT,
                    status TEXT DEFAULT 'Geplant',
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                ALTER TABLE content_plan DISABLE ROW LEVEL SECURITY;
                ```
                """)
            else:
                st.info(f"Fehler: {error_msg}")
