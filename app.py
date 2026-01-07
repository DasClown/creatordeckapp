import streamlit as st
import base64
import time

# --- 1. BOOT VERIFICATION (FAIL-SAFE) ---
# Critical: DB & Auth
critical_secrets = ["SUPABASE_URL", "SUPABASE_KEY", "RESEND_API_KEY"]
missing_critical = [s for s in critical_secrets if s not in st.secrets]

if missing_critical:
    st.error(f"KRITISCHER FEHLER: Fehlende Secrets: {missing_critical}")
    st.stop()

# Optional: Features
optional_secrets = ["RAPIDAPI_KEY", "GEMINI_API_KEY"]
missing_optional = [s for s in optional_secrets if s not in st.secrets]
if missing_optional:
    st.warning(f"Hinweis: Folgende Features sind eingeschränkt verfügbar (Keys fehlen): {missing_optional}")

# --- 2. CORE IMPORTS (DEFERRED) ---
try:
    import requests
    import toml
    import os
    import pandas as pd
    import google.genai as genai
    from supabase import create_client
    import resend
    
    # Module importieren
    from modules import crm, finance, planner, factory, gallery, channels, deals, demo
    
    # Global Clients
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    resend.api_key = st.secrets["RESEND_API_KEY"]
except Exception as e:
    st.error(f"BOOT ERROR: {e}")
    st.stop()

# --- 3. HELPER FUNCTIONS ---
@st.cache_resource
def init_supabase():
    """Initialisierte Supabase-Instanz zurückgeben (gecacht für Performance)"""
    return supabase

def send_verification_email(email):
    # WICHTIG: Im Sandbox-Modus darf NUR an deine eigene E-Mail gesendet werden.
    # WICHTIG: Absender MUSS onboarding@resend.dev sein.
    
    verify_url = f"https://www.content-core.com/?verify={email}" # Deine neue Domain
    
    try:
        params = {
            "from": "Content Core <info@content-core.com>", # Deine verifizierte Domain
            "to": [email],
            "subject": "System Activated",
            "html": f"""
                <div style='font-family: monospace; border: 1px solid #000; padding: 20px; max-width: 400px;'>
                    <h2 style='font-weight: 300; letter-spacing: -1px;'>CONTENT CORE</h2>
                    <p style='font-size: 14px;'>Engine is running. Initialisierung für: <b>{email}</b></p>
                    <hr style='border: 0; border-top: 1px solid #eee; margin: 20px 0;'>
                    <a href='{verify_url}' style='background: #000; color: #fff; padding: 10px 15px; text-decoration: none; display: inline-block; font-size: 12px;'>ACTIVATE SYSTEM</a>
                </div>
            """
        }
        
        r = resend.Emails.send(params)
        return r
    except Exception as e:
        # DIAGNOSE für den User:
        masked_key = "NICHT GESETZT"
        try:
            if resend.api_key:
                masked_key = f"{resend.api_key[:5]}...{resend.api_key[-3:]}" if len(resend.api_key) > 8 else "ZU KURZ"
        except:
            masked_key = "FEHLER BEIM LESEN"
            
        st.error(f"Resend Error: {str(e)}")
        st.info(f"🔍 DEBUG: Key='{masked_key}' | Empfänger='{email}'")
        st.info("Checkliste: 1. Key in Secrets korrekt? 2. 'Sandbox'-Limits beachtet (nur eigene Email)? 3. Leerzeichen im Key?")
        st.markdown(f"[Manuelle Verifizierung (Notfall)]({verify_url})")
        return None

def run_instagram_sync(profile_url, supabase):
    """Refined Instagram sync using the Statistics API with URL input"""
    api_url = "https://instagram-statistics-api.p.rapidapi.com/community"
    
    headers = {
        "x-rapidapi-key": st.secrets.get("RAPIDAPI_KEY"),
        "x-rapidapi-host": "instagram-statistics-api.p.rapidapi.com"
    }
    
    params = {"url": profile_url}

    try:
        with st.spinner("PENETRATING INSTAGRAM API..."):
            response = requests.get(api_url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json().get("data", {})
                
                # Daten-Payload für Supabase basierend auf API-Struktur
                stats_payload = {
                    "user_id": st.session_state.get('user_email', 'unknown'),
                    "platform": "instagram",
                    "handle": data.get("screenName"),
                    "followers": data.get("usersCount"),
                    "engagement_rate": data.get("avgER"),
                    "avg_likes": data.get("avgLikes"),
                    "quality_score": data.get("qualityScore")
                }
                
                # Speichern in die Tabelle stats_history
                supabase.table("stats_history").insert(stats_payload).execute()
                
                st.success("SYNC SUCCESSFUL")
                return True
            else:
                st.error(f"API REJECTED: {response.status_code}")
    except Exception as e:
        st.error(f"CORE CONNECTION LOST: {e}")
    return False

def render_instagram_sync(supabase, context="default"):
    """UI Komponente für den Instagram Core Sync (In Sidebar oder Landing)"""
    st.markdown("### SYSTEM CONTROL")
    
    # KEY-FIX: Dynamischer Key mit Context verhindert Duplicate Key Error
    user_email = st.session_state.get('user_email', 'guest')
    safe_email = user_email.replace('@', '_').replace('.', '_')
    unique_key = f"{context}_sync_input_{safe_email}"
    button_key = f"{context}_sync_button"
    
    user_url = st.text_input("TARGET INSTAGRAM URL", placeholder="https://instagram.com/...", key=unique_key)

    if st.button("INITIALIZE SYNC", key=button_key):
        if user_url:
            if run_instagram_sync(user_url, supabase):
                st.rerun()
        else:
            st.warning("URL erforderlich.")

# --- SETUP ---
st.set_page_config(
    page_title="CONTENT CORE",
    layout="wide"
)

# --- SETUP & STYLING ---
def render_head():
    """Render SEO and Meta Tags"""
    st.markdown("""
        <head>
            <title>CONTENT CORE | Advanced Analytics. Zero Cost. High Impact.</title>
            <meta name="description" content="Advanced Analytics für Creator. Komplett kostenlos. Alpha Access für Early Adopters.">
            <meta name="keywords" content="Content Core, Creator Analytics, Free Creator Tools, Fan Economy, Creator CRM, Content Analytics">
            <meta property="og:title" content="CONTENT CORE">
            <meta property="og:description" content="Advanced Analytics. Zero Cost. High Impact.">
            <meta property="og:type" content="website">
            <meta name="robots" content="index, follow">
        </head>
    """, unsafe_allow_html=True)
    
    # Analytics
    st.markdown("""
        <script src="https://cdn.usefathom.com/script.js" data-site="YOUR_ID" defer></script>
    """, unsafe_allow_html=True)

def render_styles():
    """Render CONTENT CORE Theme CSS"""
    st.markdown("""
    <style>
        /* Google Font: Inter Bold */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;800&display=swap');

        /* Hintergrund und Grundschrift */
        .stApp { 
            background-color: #FFFFFF; 
            color: #000000; 
        }
        
        /* Typografie: CONTENT CORE BOLD */
        h1, h2, h3, h4 { 
            font-family: 'Inter', sans-serif; 
            font-weight: 800 !important; 
            letter-spacing: -2px !important; 
            color: #000000 !important;
            text-transform: uppercase;
            text-align: center;
        }
        
        /* Buttons: CONTENT CORE SHARP */
        .stButton>button {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            border: 1px solid #000000 !important;
            border-radius: 0px !important;
            font-weight: 500 !important;
            padding: 0.5rem 2rem !important;
            transition: 0.3s !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }

        /* Metric Styling */
        .stMetric { 
            border: 1px solid #EEEEEE !important; 
            padding: 20px !important; 
            border-radius: 0px !important;
        }

        /* Input Felder: SHARP & MINIMAL */
        .stTextInput>div>div>input {
            background-color: #FFFFFF !important;
            border: 1px solid #EEEEEE !important;
            border-radius: 0px !important;
            color: #000000 !important;
            font-family: 'Inter', sans-serif;
        }

        /* Sidebar Fixes */
        [data-testid="stSidebar"] {
            background-color: #F8F8F8 !important;
            border-right: 1px solid #000000 !important;
        }

        /* Sidebar Text Visibility Fix: Wildcard für alle Elemente */
        [data-testid="stSidebar"] * {
            color: #000000 !important;
        }

        [data-testid="stSidebar"] h1 {
            text-align: left !important;
        }

        /* Metriken */
        [data-testid="stMetricValue"] {
            font-weight: 800 !important;
            letter-spacing: -2px;
            font-size: 3rem !important;
            color: #000000 !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border: none;
            color: #888888;
            font-weight: 300;
        }
        .stTabs [aria-selected="true"] {
            color: #000000 !important;
            font-weight: 800 !important;
            border-bottom: 2px solid #000000 !important;
        }

        /* Status Boxen: SHARP & CLEAN */
        div[data-testid="stNotification"] {
            border-radius: 0px !important;
            border: 1px solid #000000 !important;
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* Info Boxes - Blauer Hintergrund mit schwarzem Text */
        div[data-testid="stInfo"] {
            background-color: #E3F2FD !important;
            color: #000000 !important;
            border: 1px solid #2196F3 !important;
            border-radius: 0px !important;
        }
        div[data-testid="stInfo"] * {
            color: #000000 !important;
        }
        
        /* Warning Boxes - Gelber Hintergrund mit schwarzem Text */
        div[data-testid="stWarning"] {
            background-color: #FFF9C4 !important;
            color: #000000 !important;
            border: 1px solid #FFC107 !important;
            border-radius: 0px !important;
        }
        div[data-testid="stWarning"] * {
            color: #000000 !important;
        }
        
        /* Success Boxes - Grüner Hintergrund mit schwarzem Text */
        div[data-testid="stSuccess"] {
            background-color: #E8F5E9 !important;
            color: #000000 !important;
            border: 1px solid #4CAF50 !important;
            border-radius: 0px !important;
        }
        div[data-testid="stSuccess"] * {
            color: #000000 !important;
        }
        
        /* Error Boxes - Roter Hintergrund mit schwarzem Text */
        div[data-testid="stError"] {
            background-color: #FFEBEE !important;
            color: #000000 !important;
            border: 1px solid #F44336 !important;
            border-radius: 0px !important;
        }
        div[data-testid="stError"] * {
            color: #000000 !important;
        }
        
        /* Expander - Schwarzer Text */
        div[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #EEEEEE !important;
            border-radius: 0px !important;
        }
        div[data-testid="stExpander"] * {
            color: #000000 !important;
        }
        
        /* Markdown Text - Schwarzer Text */
        .stMarkdown {
            color: #000000 !important;
        }
        .stMarkdown * {
            color: #000000 !important;
        }
        
        /* Text Area - Schwarzer Text */
        textarea {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        
        /* Select Slider - Schwarzer Text */
        div[data-baseweb="slider"] * {
            color: #000000 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- LANDING PAGE ---
def render_landing_page():
    # Zentrales Logo
    # Zentrales Logo (mit HTML/CSS zentriert für perfekte Ausrichtung)
    with open("assets/logo_icon.jpg", "rb") as f:
        img_data = f.read()
    img_base64 = base64.b64encode(img_data).decode()
    
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <img src="data:image/jpg;base64,{img_base64}" width="120" style="border-radius: 50%;">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<h1>CONTENT CORE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>SYSTEM INITIALIZATION</p>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True)

    left_spacer, center_col, right_spacer = st.columns([1, 2, 1])

    with center_col:
        st.markdown("### JOIN THE WAITLIST")
        email = st.text_input("Deine E-Mail", placeholder="name@domain.com")
        if st.button("BEWERBEN"):
            if email:
                # Supabase initialisieren
                supabase = init_supabase()
                if supabase:
                    try:
                        # Check if email already exists and its confirm status
                        existing = supabase.table("waitlist").select("email, is_confirmed").eq("email", email).execute()
                        if existing.data and len(existing.data) > 0:
                            is_conf = existing.data[0].get("is_confirmed", False)
                            if is_conf:
                                st.info("Du bist bereits verifiziert! Klicke unten auf 'ENTER TERMINAL' zum Login.")
                            else:
                                st.warning("Du bist bereits auf der Warteliste, aber noch nicht bestätigt.")
                                if st.button("BESTÄTIGUNGS-LINK ERNEUT SENDEN", key="resend_landing"):
                                    if send_verification_email(email):
                                        st.success(f"Link erneut an {email} gesendet.")
                        else:
                            # 1. In DB speichern (is_confirmed ist default false)
                            supabase.table("waitlist").insert({"email": email}).execute()
                            
                            # 2. E-Mail versenden via Resend
                            if send_verification_email(email):
                                st.success(f"Bestätigungs-Link wurde an {email} gesendet.")
                            else:
                                st.warning("E-Mail konnte nicht gesendet werden, aber dein Eintrag wurde gespeichert.")
                            
                            st.info(f"ALPHA DEBUG: Bitte prüfe dein Postfach. Link: https://www.content-core.com/?verify={email}")
                            # In einer Alpha-Phase können wir den Link zum Testen anzeigen
                    except Exception as e:
                        st.error(f"Fehler beim Speichern: {str(e)}")
                        st.info("💡 Tipp: Falls es ein Verbindungsfehler ist, prüfe deine SUPABASE_URL in den Secrets. Prüfe auch, ob RLS für die 'waitlist' Tabelle deaktiviert ist.")
                else:
                    st.warning("Waitlist aktuell nicht verfügbar.")
            else:
                st.warning("Bitte E-Mail eingeben.")

    st.divider()
    
    # Trust & Privacy Badge
    st.markdown("""
        <div style='background: #ffffff; padding: 0px; margin: 40px 0; text-align: center;'>
            <h4 style='margin: 0 0 10px 0; font-weight: 300; font-size: 20px; color: #000000;'>Data Privacy</h4>
            <p style='margin: 0; color: #000000; font-size: 16px; line-height: 1.6; font-weight: 300; max-width: 700px; margin: 0 auto;'>
                Deine Daten werden verschlüsselt gespeichert. 
                Wir haben <span style='font-weight: 600;'>keinen Zugriff</span> auf deine Passwörter; die Verbindung erfolgt über 
                öffentliche Schnittstellen oder manuellen Import.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Admin Access (versteckt)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
        if st.button("ENTER TERMINAL", key="admin_access"):
            st.session_state.view = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- VIEW MANAGEMENT & AUTH ---
def check_access(email):
    """Prüft Zugriff - Hardcoded Admin + Datenbank-Prüfung"""
    # Hardcode für Initialzugriff während Setup
    if email == "janick@icanhasbucket.de":
        st.session_state.access_granted = True
        st.session_state.user_email = email
        return True
    
    # Reguläre Datenbank-Prüfung
    try:
        supabase = init_supabase()
        res = supabase.table("profiles").select("is_verified").eq("email", email).execute()
        if res.data and res.data[0].get("is_verified"):
            st.session_state.access_granted = True
            st.session_state.user_email = email
            return True
    except Exception as e:
        st.error(f"Datenbankfehler: {e}")
    return False

def render_auth_interface():
    """Vereinfachtes Terminal Login"""
    # Auth Logo Zentriert
    with open("assets/logo_horizontal.jpg", "rb") as f:
        img_data = f.read()
    img_base64 = base64.b64encode(img_data).decode()
    
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <img src="data:image/jpg;base64,{img_base64}" width="250">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.title("TERMINAL LOGIN")
    st.markdown("---")
    
    email_input = st.text_input("Registrierte E-Mail", key="login_email_terminal", placeholder="name@domain.com")
    
    if st.button("LOGIN", key="login_btn_terminal", use_container_width=True):
        if check_access(email_input):
            st.success("✅ Zugriff gewährt. System wird initialisiert...")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Zugriff verweigert. E-Mail nicht bestätigt oder nicht registriert.")

# --- VIRAL SHARE ---
def render_viral_share():
    st.markdown("""
        <div style='padding: 60px 20px; text-align: center;'>
            <h2 style='font-weight: 300; margin-bottom: 20px;'>ACTIVATE FULL ENGINE</h2>
            <p style='color: #666; margin-bottom: 30px; font-weight: 300;'>
                Teile CONTENT CORE auf Social Media und erhalte sofortigen Vollzugriff.<br>
                Kostenlos. Für immer.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### TWITTER/X")
        share_twitter = "https://twitter.com/intent/tweet?text=Gerade%20das%20neue%20Terminal%20von%20content-core.com%20entdeckt.%20Endlich%20Ordnung%20im%20Workflow.%20"
        if st.button("SHARE ON X", key="share_x"):
            st.session_state.full_access = True
            st.success("FULL ENGINE ACTIVATED")
            st.rerun()
        st.markdown(f"[Open Twitter/X]({share_twitter})")
    
    with col2:
        st.markdown("### REDDIT")
        share_reddit = "https://reddit.com/submit?url=https://content-core.com&title=CONTENT%20CORE%20-%20Advanced%20Analytics%20for%20Creators"
        if st.button("SHARE ON REDDIT", key="share_reddit"):
            st.session_state.full_access = True
            st.success("FULL ENGINE ACTIVATED")
            st.rerun()
        st.markdown(f"[Open Reddit]({share_reddit})")
    
    st.divider()
    if st.button("SKIP & ACTIVATE", key="skip_share"):
        st.session_state.full_access = True
        st.rerun()
# --- DASHBOARD & NAVIGATION ---
def render_dashboard_layout():
    supabase = init_supabase()
    if not supabase:
        st.error("Supabase nicht konfiguriert.")
        return

    with st.sidebar:
        st.image("assets/logo_horizontal.jpg", width=180)
        st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)
        st.info("ALPHA ACCESS: FREE FOREVER")
        
        # Navigation
        page = st.radio("NAVIGATION", ["DASHBOARD", "CHANNELS", "FACTORY", "GALLERY", "CRM", "DEALS", "FINANCE", "PLANNER", "DEMO"])
        
        st.markdown("---")
        # Sync in Sidebar integriert
        render_instagram_sync(supabase, context="sidebar")
        
        st.markdown("---")
        if st.button("LOGOUT"):
            st.session_state.access_granted = False
            st.rerun()

    if page == "DASHBOARD":
        render_dashboard(supabase)
    elif page == "GALLERY":
        gallery.render_gallery(supabase)
    elif page == "CHANNELS":
        channels.render_channels()
    elif page == "DEALS":
        deals.render_deals()
    elif page == "CRM":
        crm.render_crm(supabase)
    elif page == "FINANCE":
        finance.render_finance(supabase)
    elif page == "PLANNER":
        planner.render_planner(supabase)
    elif page == "DEMO":
        demo.render_demo()
    elif page == "FACTORY":
        factory.render_factory(supabase)

def render_dashboard(supabase):
    st.title("CONTENT CORE / ENGINE")
    user_id = st.session_state.get('user_email', 'unknown')

    try:
        stats = supabase.table("stats_history").select("*").eq("user_id", user_id).execute()
        
        if not stats.data:
            st.markdown("### System Initialization")
            st.info("Willkommen im Terminal. Lade deine ersten Daten.")
            col1, col2 = st.columns(2)
            with col1:
                render_instagram_sync(supabase, context="onboarding")
            with col2:
                st.markdown("#### Option B: Manual Data Entry")
                with st.expander("Eckdaten eingeben"):
                    followers = st.number_input("Follower", value=1000)
                    engagement = st.number_input("Engagement Rate (%)", value=3.5, step=0.1)
                    quality = st.number_input("Quality Score", value=7.0, step=0.1)
                    if st.button("Initialize"):
                        supabase.table("stats_history").insert({
                            "user_id": user_id,
                            "platform": "instagram",
                            "handle": "manual_entry",
                            "followers": int(followers),
                            "engagement_rate": engagement / 100,
                            "avg_likes": int(followers * engagement / 100),
                            "quality_score": quality
                        }).execute()
                        st.rerun()
        else:
            # Holen der neuesten Daten
            latest_stats = supabase.table("stats_history")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if latest_stats.data:
                latest = latest_stats.data[0]
                
                # KPI GRID (4 Spalten) - mit None-Checks
                col1, col2, col3, col4 = st.columns(4)
                
                # Sichere Werte mit Fallbacks
                followers = latest.get('followers') or 0
                engagement = latest.get('engagement_rate') or 0.0
                quality = latest.get('quality_score') or 0.0
                
                col1.metric("FOLLOWERS", f"{int(followers):,}")
                col2.metric("ENGAGEMENT", f"{float(engagement):.2%}")
                col3.metric("CORE SCORE", f"{float(quality):.1f}")
                col4.metric("REACH INDEX", f"{int(followers * 0.12):,}") # Kalkulierter Wert

                # ANALYTICS GRAPH
                st.markdown("### GROWTH TRAJECTORY")
                # Verlauf aus den letzten 10 Einträgen
                history_query = supabase.table("stats_history")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .order("created_at", desc=True)\
                    .limit(10)\
                    .execute()
                
                if history_query.data:
                    df = pd.DataFrame(history_query.data)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    # Wir drehen das DF um, damit der Trend von alt nach neu geht
                    st.line_chart(df.sort_values("created_at").set_index("created_at")["followers"])
                    
                    # RAW DATA TABELLE
                    with st.expander("VIEW RAW SYSTEM DATA"):
                        st.table(df[["created_at", "handle", "followers", "quality_score"]])
                else:
                    st.info("KEINE DATEN IM CORE. NUTZE DIE SIDEBAR FÜR DEN ERSTEN SYNC.")
                
                st.markdown("---")
                st.markdown(f"**LOGGED AS:** {user_id} | **STATUS:** CORE ACTIVE")
    except Exception as e:
        st.error(f"ENGINE CRITICAL ERROR: {e}")

# --- MAIN ORCHESTRATION ---
def main():
    render_head()
    render_styles()
    
    if "access_granted" not in st.session_state:
        st.session_state.access_granted = False
    if "view" not in st.session_state:
        st.session_state.view = "landing"
    if "full_access" not in st.session_state:
        st.session_state.full_access = False

    # URL Verification Handler
    if "verify" in st.query_params:
        email = st.query_params["verify"]
        supabase = init_supabase()
        if supabase:
            try:
                supabase.table("waitlist").update({"is_confirmed": True}).eq("email", email).execute()
                st.success(f"Email {email} confirmed! Login now.")
            except Exception as e: st.error(f"Error: {e}")

    # Routing
    if not st.session_state.access_granted:
        if st.session_state.view == "landing":
            render_landing_page()
        else:
            render_auth_interface()
    else:
        if not st.session_state.full_access:
            render_viral_share()
        else:
            render_dashboard_layout()

if __name__ == "__main__":
    main()
