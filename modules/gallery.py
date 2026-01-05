import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

def render_gallery():
    st.title("🖼️ MEDIA HUB")
    st.markdown("Upload & Branding Tool")

    uploaded_file = st.file_uploader("Bild auswählen", type=["jpg", "png", "jpeg"])
    watermark_text = st.text_input("Wasserzeichen Text", "CREATOR.TECH")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        if st.button("BRAND IMAGE ⚡"):
            # Bildverarbeitung
            draw = ImageDraw.Draw(image)
            # Einfaches Wasserzeichen unten rechts
            width, height = image.size
            draw.text((width - 150, height - 30), watermark_text, fill=(255, 255, 255))
            
            st.image(image, caption="Branded Image", use_container_width=True)
            
            # Download Button
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            st.download_button("Download Branded Image", buf.getvalue(), "branded_image.png", "image/png")
