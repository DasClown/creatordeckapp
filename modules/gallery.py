import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import uuid

def render_gallery(supabase):
    st.title("GALLERY")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload & Brand")
        uploaded_file = st.file_uploader("Bild wählen", type=["jpg", "png", "jpeg"])
        
        # Erweiterte Watermark-Optionen
        st.markdown("#### Watermark Einstellungen")
        wm_text = st.text_input("Watermark Text", "CONTENT CORE")
        
        col_a, col_b = st.columns(2)
        with col_a:
            opacity = st.slider("Deckkraft (%)", 0, 100, 80)
            font_size = st.slider("Schriftgröße", 20, 100, 40)
        with col_b:
            position = st.selectbox("Position", [
                "Unten Rechts",
                "Unten Links", 
                "Oben Rechts",
                "Oben Links",
                "Mitte"
            ])
        
        # Optionales Logo
        logo_file = st.file_uploader("Logo (optional)", type=["png"], key="logo_upload")
        
        if uploaded_file:
            img = Image.open(uploaded_file).convert("RGBA")
            
            # Vorschau mit Watermark
            preview_img = img.copy()
            
            # Text-Watermark hinzufügen
            if wm_text:
                # Transparente Overlay-Ebene
                txt_layer = Image.new('RGBA', preview_img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(txt_layer)
                
                # Font (fallback auf default)
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Position berechnen
                w, h = preview_img.size
                bbox = draw.textbbox((0, 0), wm_text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                
                if position == "Unten Rechts":
                    x, y = w - text_w - 20, h - text_h - 20
                elif position == "Unten Links":
                    x, y = 20, h - text_h - 20
                elif position == "Oben Rechts":
                    x, y = w - text_w - 20, 20
                elif position == "Oben Links":
                    x, y = 20, 20
                else:  # Mitte
                    x, y = (w - text_w) // 2, (h - text_h) // 2
                
                # Text mit Deckkraft
                alpha = int(255 * (opacity / 100))
                draw.text((x, y), wm_text, fill=(255, 255, 255, alpha), font=font)
                
                # Overlay kombinieren
                preview_img = Image.alpha_composite(preview_img, txt_layer)
            
            # Logo hinzufügen (falls vorhanden)
            if logo_file:
                logo = Image.open(logo_file).convert("RGBA")
                # Logo skalieren (max 20% der Bildbreite)
                logo_w = int(w * 0.2)
                logo_h = int(logo.height * (logo_w / logo.width))
                logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                
                # Logo-Position (immer oben links)
                logo_x, logo_y = 20, 20
                
                # Logo mit Deckkraft
                if opacity < 100:
                    logo_alpha = logo.split()[3]
                    logo_alpha = logo_alpha.point(lambda p: int(p * (opacity / 100)))
                    logo.putalpha(logo_alpha)
                
                preview_img.paste(logo, (logo_x, logo_y), logo)
            
            # Vorschau anzeigen
            st.image(preview_img, caption="Vorschau", use_container_width=True)
            
            if st.button("PROCESS & UPLOAD"):
                # Finales Bild speichern (mit Watermark)
                final_img = preview_img.convert("RGB")  # Konvertiere zu RGB für JPEG
                buf = io.BytesIO()
                final_img.save(buf, format="PNG")
                buf.seek(0)
                
                try:
                    file_path = f"branded/{uuid.uuid4()}.png"
                    
                    # Upload zu Supabase Storage
                    supabase.storage.from_("assets").upload(file_path, buf.getvalue())
                    st.success(f"Stored as: {file_path}")
                except Exception as e:
                    error_msg = str(e)
                    
                    # Spezielle Behandlung für Storage-Fehler
                    if "Bucket not found" in error_msg or "404" in error_msg:
                        st.error("🗂️ **SUPABASE STORAGE BUCKET FEHLT**")
                        st.warning("""
                        Der 'assets' Bucket existiert nicht in Supabase. So erstellst du ihn:
                        
                        1. Gehe zu [Supabase Dashboard](https://supabase.com/dashboard)
                        2. Wähle dein Projekt
                        3. Storage → "New Bucket"
                        4. Name: `assets`
                        5. Public: ✅ (für Bild-URLs)
                        
                        **Alternative:** GALLERY-Feature vorübergehend nicht nutzen
                        """)
                    elif "Policy" in error_msg or "permission" in error_msg.lower():
                        st.error("🔒 **STORAGE PERMISSIONS FEHLEN**")
                        st.warning("""
                        Keine Upload-Berechtigung. Prüfe Storage Policies:
                        
                        1. Supabase Dashboard → Storage → assets
                        2. Policies → "New Policy"
                        3. Erlaube INSERT für authenticated users
                        """)
                    else:
                        st.error(f"Upload fehlgeschlagen: {error_msg}")
                        st.info("Tipp: Prüfe Supabase Storage Konfiguration")

    with col2:
        st.subheader("Cloud Assets")
        # Liste der letzten 5 Uploads anzeigen
        try:
            files = supabase.storage.from_("assets").list("branded")
            if files:
                for f in files[-5:]:
                    url = supabase.storage.from_("assets").get_public_url(f"branded/{f['name']}")
                    st.image(url, width=200)
                    st.caption(f['name'])
            else:
                st.info("Noch keine Uploads vorhanden.")
        except:
            st.info("Keine Assets gefunden.")
