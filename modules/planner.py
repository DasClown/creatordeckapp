import streamlit as st

def render_planner(supabase):
    st.title("CONTENT PLANNER")
    
    st.error("⚠️ **PLANNER MODUL DEAKTIVIERT**")
    
    st.markdown("""
    Das PLANNER-Modul ist temporär deaktiviert weil die existierende `content_plan` Tabelle 
    ein unbekanntes Schema hat.
    
    ## 🔧 Lösung: Tabelle neu erstellen
    
    **Option 1: Alte Tabelle löschen und neu erstellen**
    
    1. Gehe zu **Supabase Dashboard** → **SQL Editor**
    2. Führe aus:
    
    ```sql
    -- Alte Tabelle löschen (ACHTUNG: Alle Daten gehen verloren!)
    DROP TABLE IF EXISTS content_plan;
    
    -- Neue Tabelle mit korrektem Schema erstellen
    CREATE TABLE content_plan (
        id SERIAL PRIMARY KEY,
        publish_date TEXT NOT NULL,
        platform TEXT DEFAULT 'Instagram',
        c_type TEXT DEFAULT 'Post',
        title TEXT,
        caption TEXT,
        asset_url TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- RLS deaktivieren
    ALTER TABLE content_plan DISABLE ROW LEVEL SECURITY;
    ```
    
    **Option 2: Existierende Tabelle erweitern**
    
    Wenn du Daten behalten möchtest, füge fehlende Spalten hinzu:
    
    ```sql
    -- Fehlende Spalten hinzufügen (falls sie nicht existieren)
    ALTER TABLE content_plan ADD COLUMN IF NOT EXISTS publish_date TEXT;
    ALTER TABLE content_plan ADD COLUMN IF NOT EXISTS c_type TEXT;
    ALTER TABLE content_plan ADD COLUMN IF NOT EXISTS title TEXT;
    ALTER TABLE content_plan ADD COLUMN IF NOT EXISTS caption TEXT;
    ALTER TABLE content_plan ADD COLUMN IF NOT EXISTS asset_url TEXT;
    ```
    
    ---
    
    ## ℹ️ Alternative
    
    Nutze andere Module:
    - **DASHBOARD** - Instagram Analytics
    - **GALLERY** - Bild-Branding
    - **FACTORY** - AI Content-Generierung
    - **CRM** - Deal-Management
    
    Nach dem Setup wird PLANNER automatisch wieder funktionieren!
    """)
