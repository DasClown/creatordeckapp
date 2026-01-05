import streamlit as st
from PIL import Image, ImageDraw
import io
import uuid

def render_gallery(supabase):
    st.title("GALLERY")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload & Brand")
        uploaded_file = st.file_uploader("Bild wählen", type=["jpg", "png", "jpeg"])
        wm_text = st.text_input("Watermark", "CREATOR.TECH")
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            if st.button("PROCESS & UPLOAD"):
                # Branding Logik
                draw = ImageDraw.Draw(img)
                w, h = img.size
                draw.text((w-150, h-50), wm_text, fill=(255,255,255))
                
                # In Buffer speichern
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                file_path = f"branded/{uuid.uuid4()}.png"
                
                # Upload zu Supabase Storage
                supabase.storage.from_("assets").upload(file_path, buf.getvalue())
                st.success(f"Stored as: {file_path}")

    with col2:
        st.subheader("Cloud Assets")
        # Liste der letzten 5 Uploads anzeigen
        files = supabase.storage.from_("assets").list("branded")
        for f in files[-5:]:
            url = supabase.storage.from_("assets").get_public_url(f"branded/{f['name']}")
            st.image(url, width=200)
            st.caption(f['name'])
