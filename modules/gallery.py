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
            # Bild laden und zu RGB konvertieren
            img = Image.open(uploaded_file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Vorschau mit Watermark erstellen
            preview_img = img.copy()
            
            # Text-Watermark hinzufügen
            if wm_text:
                # Direkt auf das Bild zeichnen (einfacher Ansatz)
                draw = ImageDraw.Draw(preview_img)
                
                # Font laden - mit robustem Fallback
                font = None
                font_paths = [
                    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
                ]
                
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
                
                # Fallback auf default font
                if font is None:
                    font = ImageFont.load_default()
                
                # Position berechnen
                w, h = preview_img.size
                
                # Text-Größe ermitteln
                try:
                    bbox = draw.textbbox((0, 0), wm_text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                except:
                    # Fallback für ältere PIL-Versionen
                    text_w, text_h = draw.textsize(wm_text, font=font)
                
                # Position berechnen
                padding = 20
                if position == "Unten Rechts":
                    x, y = w - text_w - padding, h - text_h - padding
                elif position == "Unten Links":
                    x, y = padding, h - text_h - padding
                elif position == "Oben Rechts":
                    x, y = w - text_w - padding, padding
                elif position == "Oben Links":
                    x, y = padding, padding
                else:  # Mitte
                    x, y = (w - text_w) // 2, (h - text_h) // 2
                
                # Schatten für bessere Lesbarkeit
                shadow_offset = 2
                draw.text((x + shadow_offset, y + shadow_offset), wm_text, fill=(0, 0, 0), font=font)
                
                # Haupttext in Weiß
                draw.text((x, y), wm_text, fill=(255, 255, 255), font=font)
            
            # Logo hinzufügen (falls vorhanden)
            if logo_file:
                try:
                    logo = Image.open(logo_file).convert("RGBA")
                    w, h = preview_img.size
                    
                    # Logo skalieren (max 20% der Bildbreite)
                    logo_w = int(w * 0.2)
                    logo_h = int(logo.height * (logo_w / logo.width))
                    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                    
                    # Logo-Position (oben links mit Padding)
                    logo_x, logo_y = 20, 20
                    
                    # Logo einfügen
                    preview_img.paste(logo, (logo_x, logo_y), logo)
                except Exception as e:
                    st.warning(f"Logo konnte nicht hinzugefügt werden: {str(e)}")
            
            # Vorschau anzeigen
            st.image(preview_img, caption="Vorschau", use_container_width=True)
            
            # Download-Button für Vorschau
            buf_preview = io.BytesIO()
            preview_img.save(buf_preview, format="PNG")
            buf_preview.seek(0)
            
            st.download_button(
                label="📥 DOWNLOAD PREVIEW",
                data=buf_preview,
                file_name=f"preview_{uploaded_file.name}",
                mime="image/png"
            )
            
            if st.button("☁️ UPLOAD TO CLOUD"):
                # Finales Bild speichern
                buf = io.BytesIO()
                preview_img.save(buf, format="PNG")
                buf.seek(0)
                
                try:
                    file_path = f"branded/{uuid.uuid4()}.png"
                    
                    # Upload zu Supabase Storage
                    supabase.storage.from_("assets").upload(file_path, buf.getvalue())
                    st.success(f"✅ Uploaded: {file_path}")
                    
                    # Public URL anzeigen
                    url = supabase.storage.from_("assets").get_public_url(file_path)
                    st.info(f"🔗 Public URL: {url}")
                    
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
                        """)
                    elif "Policy" in error_msg or "permission" in error_msg.lower():
                        st.error("🔒 **STORAGE PERMISSIONS FEHLEN**")
                        st.warning("""
                        Keine Upload-Berechtigung. Prüfe Storage Policies:
                        
                        1. Supabase Dashboard → SQL Editor
                        2. Führe aus: `CREATE POLICY "Allow anonymous uploads" ON storage.objects FOR INSERT TO anon WITH CHECK (bucket_id = 'assets');`
                        """)
                    else:
                        st.error(f"Upload fehlgeschlagen: {error_msg}")
                        st.info("Tipp: Prüfe Supabase Storage Konfiguration")

    with col2:
        st.subheader("Cloud Assets")
        # Liste der letzten 5 Uploads anzeigen
        try:
            files = supabase.storage.from_("assets").list("branded")
            
            # Filter out placeholder files
            real_files = [f for f in files if f.get('name') and not f['name'].startswith('.')]
            
            if real_files:
                st.caption(f"📁 {len(real_files)} Assets verfügbar")
                
                for idx, f in enumerate(real_files[-5:]):  # Zeige die letzten 5
                    file_name = f['name']
                    url = supabase.storage.from_("assets").get_public_url(f"branded/{file_name}")
                    
                    # Container für jedes Asset
                    with st.container():
                        st.image(url, width=200)
                        st.caption(file_name)
                        
                        # Buttons in einer Zeile - dezent
                        col_download, col_delete = st.columns([1, 1])
                        
                        with col_download:
                            st.markdown(f"[📥 Download]({url})")
                        
                        with col_delete:
                            # Eindeutiger Key für jeden Delete-Button
                            delete_key = f"delete_{file_name}_{idx}"
                            # Kleiner, dezenter Button
                            if st.button("🗑️", key=delete_key, help="Löschen", use_container_width=False):
                                try:
                                    # Asset aus Supabase Storage löschen
                                    supabase.storage.from_("assets").remove([f"branded/{file_name}"])
                                    st.success(f"✅ {file_name} wurde gelöscht!")
                                    st.rerun()
                                except Exception as delete_error:
                                    st.error(f"❌ Fehler beim Löschen: {str(delete_error)}")
                        
                        st.divider()
            else:
                st.info("💡 Noch keine Assets hochgeladen. Lade dein erstes Bild hoch!")
        except Exception as e:
            st.info("💡 Noch keine Assets vorhanden. Erstelle den 'assets' Bucket in Supabase Storage.")
