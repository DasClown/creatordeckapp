import streamlit as st
import pandas as pd
from datetime import datetime

def render_planner(supabase):
    st.title("PLANNER")
    
    # Content-Kalender aus DB laden
    try:
        res = supabase.table("content_calendar").select("*").execute()
        
        if not res.data:
            st.info("Noch keine Content-Planung. Erstelle deinen ersten Post!")
            df_calendar = pd.DataFrame(columns=["date", "platform", "content_type", "status", "notes"])
        else:
            df_calendar = pd.DataFrame(res.data)
            
            # Stelle sicher dass alle erforderlichen Spalten existieren
            required_cols = ["date", "platform", "content_type", "status", "notes"]
            for col in required_cols:
                if col not in df_calendar.columns:
                    df_calendar[col] = ""
        
        # UI
        st.subheader("Content Calendar")
        edited_df = st.data_editor(
            df_calendar[["date", "platform", "content_type", "status", "notes"]], 
            width="stretch", 
            hide_index=True, 
            num_rows="dynamic"
        )
        
        if st.button("SAVE CALENDAR"):
            try:
                # Logik zum Updaten/Einfügen in Supabase
                for index, row in edited_df.iterrows():
                    # Skip leere Zeilen
                    if not row.get("date") and not row.get("platform"):
                        continue
                        
                    calendar_data = {
                        "date": str(row.get("date", "")),
                        "platform": str(row.get("platform", "Instagram")),
                        "content_type": str(row.get("content_type", "Post")),
                        "status": str(row.get("status", "Planned")),
                        "notes": str(row.get("notes", ""))
                    }
                    
                    # Prüfe ob Eintrag bereits existiert (hat ID)
                    if index < len(res.data) and "id" in res.data[index]:
                        # Update existierender Eintrag
                        entry_id = res.data[index]["id"]
                        supabase.table("content_calendar").update(calendar_data).eq("id", entry_id).execute()
                    else:
                        # Neuer Eintrag
                        supabase.table("content_calendar").insert(calendar_data).execute()
                
                st.success("Kalender gespeichert!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Speichern: {str(e)}")
                
    except Exception as e:
        error_msg = str(e)
        st.error("PLANNER Fehler")
        
        if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            st.warning("""
            **Die 'content_calendar' Tabelle fehlt in Supabase.**
            
            Erstelle sie mit dieser SQL-Query:
            
            ```sql
            CREATE TABLE IF NOT EXISTS content_calendar (
                id SERIAL PRIMARY KEY,
                date TEXT,
                platform TEXT DEFAULT 'Instagram',
                content_type TEXT DEFAULT 'Post',
                status TEXT DEFAULT 'Planned',
                notes TEXT,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            ALTER TABLE content_calendar DISABLE ROW LEVEL SECURITY;
            ```
            
            **Alternative:** PLANNER-Feature vorübergehend nicht nutzen
            """)
        else:
            st.info(f"Fehler: {error_msg}")
