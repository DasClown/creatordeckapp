import streamlit as st

# --- 1. BOOT VERIFICATION (FAIL-SAFE) ---
required_secrets = ["SUPABASE_URL", "SUPABASE_KEY", "RAPIDAPI_KEY", "RESEND_API_KEY", "GEMINI_API_KEY"]
missing = [s for s in required_secrets if s not in st.secrets]

if missing:
    st.error(f"KRITISCHER FEHLER: Fehlende Secrets: {missing}")
    st.stop()

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
def init_supabase():
    """Initialisierte Supabase-Instanz zurückgeben"""
    return supabase

def send_verification_email(email):
    # WICHTIG: Im Sandbox-Modus darf NUR an deine eigene E-Mail gesendet werden.
    # WICHTIG: Absender MUSS onboarding@resend.dev sein.
    
    verify_url = f"https://www.content-core.io/?verify={email}" # Deine neue Domain
    
    try:
        params = {
            "from": "CONTENT-CORE <onboarding@resend.dev>",
            "to": [email],
            "subject": "Systemzugriff: CONTENT CORE verifizieren",
            "html": f"""
                <div style='font-family: monospace; border: 1px solid #000; padding: 20px; max-width: 400px;'>
                    <h2 style='font-weight: 300; letter-spacing: -1px;'>CONTENT CORE</h2>
                    <p style='font-size: 14px;'>Initialisierung des Terminals für: <b>{email}</b></p>
                    <hr style='border: 0; border-top: 1px solid #eee; margin: 20px 0;'>
                    <a href='{verify_url}' style='background: #000; color: #fff; padding: 10px 15px; text-decoration: none; display: inline-block; font-size: 12px;'>VERIFY ACCESS</a>
                </div>
            """
        }
        
        r = resend.Emails.send(params)
        return r
    except Exception as e:
        st.error(f"Resend Error: {str(e)}")
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

def render_instagram_sync(supabase):
    """UI Komponente für den Instagram Core Sync (In Sidebar oder Landing)"""
    st.markdown("### SYSTEM CONTROL")
    # Einzigartiger Key: 'engine_sync_input'
    user_url = st.text_input("TARGET INSTAGRAM URL", placeholder="https://instagram.com/...", key="engine_sync_input")

    if st.button("INITIALIZE SYNC", key="engine_sync_button"):
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
    </style>
    """, unsafe_allow_html=True)

# --- LANDING PAGE ---
def render_landing_page():
    # Zentrales Logo
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.image("assets/logo_symbol.jpg", width="stretch")
    
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
                            
                            st.info(f"ALPHA DEBUG: Bitte prüfe dein Postfach. Link: https://www.content-core.io/?verify={email}")
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
                Deine Daten werden verschlüsselt in einer dedizierten Supabase-Instanz gespeichert. 
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
def render_auth_interface():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image("assets/logo_full.jpg", width="stretch")
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["REGISTRIERUNG", "LOGIN"])
    
    with auth_tab1:
        st.markdown("### ZUGANG ANFORDERN")
        new_email = st.text_input("E-Mail für Warteliste", key="reg_email")
        if st.button("ZUGANG ANFORDERN", key="reg_btn"):
            if new_email:
                supabase = init_supabase()
                if supabase:
                    try:
                        existing = supabase.table("waitlist").select("email, is_confirmed").eq("email", new_email).execute()
                        if existing.data and len(existing.data) > 0:
                            is_conf = existing.data[0].get("is_confirmed", False)
                            if is_conf:
                                st.info("Du bist bereits verifiziert! Nutze den LOGIN Tab.")
                            else:
                                st.warning("Du bist bereits auf der Warteliste, aber noch nicht bestätigt.")
                                if st.button("BESTÄTIGUNGS-LINK ERNEUT SENDEN"):
                                    if send_verification_email(new_email):
                                        st.success(f"Link erneut an {new_email} gesendet.")
                        else:
                            supabase.table("waitlist").insert({"email": new_email, "is_confirmed": False}).execute()
                            if send_verification_email(new_email):
                                st.success(f"Bestätigungs-Link an {new_email} gesendet. Bitte prüfe dein Postfach.")
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                else:
                    st.error("Datenbank nicht erreichbar.")
            else:
                st.error("Bitte E-Mail eingeben.")

    with auth_tab2:
        st.markdown("### TERMINAL LOGIN")
        login_email = st.text_input("Registrierte E-Mail", placeholder="name@domain.com", key="login_email_input")
        if st.button("BOOT SYSTEM", key="login_btn"):
            if login_email:
                supabase = init_supabase()
                if supabase:
                    try:
                        check = supabase.table("waitlist").select("is_confirmed").eq("email", login_email).execute()
                        if check.data and len(check.data) > 0 and check.data[0]['is_confirmed']:
                            st.session_state.authenticated = True
                            st.session_state.user_email = login_email
                            st.success("System Boot Sequence Initialized.")
                            st.rerun()
                        else:
                            st.error("Zugriff verweigert. E-Mail nicht bestätigt oder nicht registriert.")
                    except Exception as e:
                        st.error(f"Datenbank-Fehler: {e}")
                else:
                    st.error("Supabase-Verbindung fehlgeschlagen.")
            else:
                st.warning("Bitte E-Mail eingeben.")

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
        share_twitter = "https://twitter.com/intent/tweet?text=Gerade%20das%20neue%20Terminal%20von%20content-core.io%20entdeckt.%20Endlich%20Ordnung%20im%20Workflow.%20"
        if st.button("SHARE ON X", key="share_x"):
            st.session_state.full_access = True
            st.success("FULL ENGINE ACTIVATED")
            st.rerun()
        st.markdown(f"[Open Twitter/X]({share_twitter})")
    
    with col2:
        st.markdown("### REDDIT")
        share_reddit = "https://reddit.com/submit?url=https://content-core.io&title=CONTENT%20CORE%20-%20Advanced%20Analytics%20for%20Creators"
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
        st.image("assets/logo_full.jpg", width="stretch")
        st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)
        st.info("ALPHA ACCESS: FREE FOREVER")
        
        # Navigation
        page = st.radio("NAVIGATION", ["DASHBOARD", "CHANNELS", "FACTORY", "GALLERY", "CRM", "DEALS", "FINANCE", "PLANNER", "DEMO"])
        
        st.markdown("---")
        # Sync in Sidebar integriert
        render_instagram_sync(supabase)
        
        st.markdown("---")
        if st.button("LOGOUT"):
            st.session_state.authenticated = False
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
                render_instagram_sync(supabase)
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
                
                # KPI GRID (4 Spalten)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("FOLLOWERS", f"{int(latest['followers']):,}")
                col2.metric("ENGAGEMENT", f"{float(latest['engagement_rate']):.2%}")
                col3.metric("CORE SCORE", f"{float(latest['quality_score']):.1f}")
                col4.metric("REACH INDEX", f"{int(latest['followers'] * 0.12):,}") # Kalkulierter Wert

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
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
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
    if not st.session_state.authenticated:
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
    if "user_email" not in st.session_state:
        st.session_state.user_email = "janick@icanhasbucket.de" # Fallback für Test
    main()
