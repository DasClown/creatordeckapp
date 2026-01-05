import streamlit as st
import toml
import os

# Module importieren
from modules import crm, finance, planner, factory, gallery, channels, deals, demo
import pandas as pd
import google.generativeai as genai
from supabase import create_client
import resend

# --- HELPER FUNCTIONS ---
def init_supabase():
    """Initialize Supabase client with validation"""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
        if not url or not key:
            return None
            
        # Cleanup and Validation
        url = url.strip().rstrip("/")
        
        if not url.startswith("https://"):
            st.error("🚫 SUPABASE_URL muss mit 'https://' beginnen.")
            return None
        
        if ".supabase.co" not in url:
            st.error("🚫 SUPABASE_URL scheint kein gültiger Supabase-Endpunkt zu sein.")
            return None

        return create_client(url, key)
    except Exception as e:
        st.error(f"🔧 Interner Fehler bei Supabase-Initialisierung: {e}")
        return None

def send_verification_email(email, confirmation_url):
    """Send verification email via Resend"""
    try:
        resend.api_key = st.secrets.get("RESEND_API_KEY", "re_P9igZ7ze_L3JmWkdRe3KEJWW9FBpTP6aT")
        
        r = resend.Emails.send({
            "from": "CREATOR.FANS <onboarding@resend.dev>",
            "to": email,
            "subject": "Verifiziere deinen Zugang zu CREATOR.FANS",
            "html": f"""
                <div style='font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee;'>
                    <h2 style='font-weight: 300;'>Willkommen bei CREATOR.FANS</h2>
                    <p>Klicke auf den folgenden Link, um deine E-Mail zu bestätigen und dein Terminal freizuschalten:</p>
                    <a href='{confirmation_url}' style='display: inline-block; padding: 10px 20px; background-color: #000; color: #fff; text-decoration: none; margin: 20px 0;'>ZUGANG VERIFIZIEREN</a>
                    <p style='color: #666; font-size: 12px;'>Falls du dich nicht registriert hast, kannst du diese Mail ignorieren.</p>
                </div>
            """
        })
        return True
    except Exception as e:
        st.error(f"Fehler beim Senden der Mail: {e}")
        return False

# --- SETUP ---
st.set_page_config(
    page_title="CREATOR.FANS",
    page_icon="🚀",
    layout="wide"
)

# --- SETUP & STYLING ---
def render_head():
    """Render SEO and Meta Tags"""
    st.markdown("""
        <head>
            <title>CREATOR.FANS | Advanced Analytics. Zero Cost. High Impact.</title>
            <meta name="description" content="Advanced Analytics für Creator. Komplett kostenlos. Alpha Access für Early Adopters.">
            <meta name="keywords" content="Creator Analytics, Free Creator Tools, Fan Economy, Creator CRM, Content Analytics">
            <meta property="og:title" content="CREATOR.FANS">
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
            letter-spacing: -1.5px !important; 
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
            transition: 0.2s !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stButton>button:hover {
            background-color: #FFFFFF !important;
            color: #000000 !important;
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
            background-color: #FFFFFF !important;
            border-right: 1px solid #EEEEEE !important;
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
    # Zentrales Logo (Punkt mit Kreisen)
    st.markdown("<div style='text-align: center; padding: 50px;'>●</div>", unsafe_allow_html=True)
    
    st.markdown("<h1>CONTENT CORE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>SYSTEM INITIALIZATION</p>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
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
                                st.info("ℹ️ Du bist bereits verifiziert! Klicke unten auf 'ENTER TERMINAL' zum Login.")
                            else:
                                st.warning("ℹ️ Du bist bereits auf der Warteliste, aber noch nicht bestätigt.")
                                if st.button("BESTÄTIGUNGS-LINK ERNEUT SENDEN", key="resend_landing"):
                                    c_url = f"https://www.creator.fans/?verify={email}"
                                    if send_verification_email(email, c_url):
                                        st.success(f"✅ Link erneut an {email} gesendet.")
                                        st.info(f"DEBUG LINK: {c_url}")
                        else:
                            # 1. In DB speichern (is_confirmed ist default false)
                            supabase.table("waitlist").insert({"email": email}).execute()
                            
                            # 2. Bestätigungs-Link generieren
                            confirmation_url = f"https://www.creator.fans/?verify={email}"
                            
                            # 3. E-Mail versenden via Resend
                            if send_verification_email(email, confirmation_url):
                                st.success(f"✅ Bestätigungs-Link wurde an {email} gesendet.")
                            else:
                                st.warning("⚠️ E-Mail konnte nicht gesendet werden, aber dein Eintrag wurde gespeichert.")
                            
                            st.info("🚀 ALPHA DEBUG: Bitte prüfe dein Postfach (auch Spam). Link: " + confirmation_url)
                            # In einer Alpha-Phase können wir den Link zum Testen anzeigen
                    except Exception as e:
                        st.error(f"Fehler beim Speichern: {str(e)}")
                        st.info("💡 Tipp: Falls es ein Verbindungsfehler ist, prüfe deine SUPABASE_URL in den Secrets. Prüfe auch, ob RLS für die 'waitlist' Tabelle deaktiviert ist.")
                else:
                    st.warning("Waitlist aktuell nicht verfügbar.")
            else:
                st.warning("Bitte E-Mail eingeben.")
    
    with col2:
        st.markdown("### CONNECT & NETWORK")
        st.write("Für Partnerschaften oder direkten Zugang kontaktiere mich über:")
        
        # Stilvolle Black-Buttons für Socials
        st.markdown("""
            <a href='https://reddit.com/u/YourUser' target='_blank' style='text-decoration:none;'>
                <div style='padding:10px; border:1px solid #000; color:#000; text-align:center; margin-bottom:10px; transition: all 0.3s;'>REDDIT</div>
            </a>
            <a href='https://instagram.com/YourUser' target='_blank' style='text-decoration:none;'>
                <div style='padding:10px; border:1px solid #000; color:#000; text-align:center;'>INSTAGRAM</div>
            </a>
        """, unsafe_allow_html=True)

    st.divider()
    
    # Trust & Privacy Badge
    st.markdown("""
        <div style='background: #ffffff; padding: 0px; margin: 40px 0; text-align: center;'>
            <h4 style='margin: 0 0 10px 0; font-weight: 300; font-size: 20px; color: #000000;'>🔒 Data Privacy</h4>
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
    st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>CREATOR.FANS</h1>", unsafe_allow_html=True)
    
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
                                st.info("ℹ️ Du bist bereits verifiziert! Nutze den LOGIN Tab.")
                            else:
                                st.warning("ℹ️ Du bist bereits auf der Warteliste, aber noch nicht bestätigt.")
                                if st.button("BESTÄTIGUNGS-LINK ERNEUT SENDEN"):
                                    conf_url = f"https://www.creator.fans/?verify={new_email}"
                                    if send_verification_email(new_email, conf_url):
                                        st.success(f"✅ Link erneut an {new_email} gesendet.")
                        else:
                            supabase.table("waitlist").insert({"email": new_email, "is_confirmed": False}).execute()
                            conf_url = f"https://www.creator.fans/?verify={new_email}"
                            if send_verification_email(new_email, conf_url):
                                st.success(f"✅ Bestätigungs-Link an {new_email} gesendet. Bitte prüfe dein Postfach.")
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
                            st.success("🔓 System Boot Sequence Initialized.")
                            st.rerun()
                        else:
                            st.error("❌ Zugriff verweigert. E-Mail nicht bestätigt oder nicht registriert.")
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
            <h2 style='font-weight: 300; margin-bottom: 20px;'>🔓 ACTIVATE FULL ENGINE</h2>
            <p style='color: #666; margin-bottom: 30px; font-weight: 300;'>
                Teile CREATOR.FANS auf Social Media und erhalte sofortigen Vollzugriff.<br>
                Kostenlos. Für immer.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🐦 TWITTER/X")
        share_twitter = "https://twitter.com/intent/tweet?text=Gerade%20das%20neue%20Terminal%20von%20creator.fans%20entdeckt.%20Endlich%20Ordnung%20im%20Workflow.%20%F0%9F%94%A5"
        st.markdown(f"<a href='{share_twitter}' target='_blank' style='text-decoration:none;'><div style='padding:15px; border:1px solid #000; color:#000; text-align:center; background:#fff;'>TWEET & UNLOCK</div></a>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🔴 REDDIT")
        share_reddit = "https://www.reddit.com/submit?title=CREATOR.FANS%20-%20Advanced%20Analytics%20for%20Creators&url=https://creator.fans"
        st.markdown(f"<a href='{share_reddit}' target='_blank' style='text-decoration:none;'><div style='padding:15px; border:1px solid #000; color:#000; text-align:center; background:#fff;'>POST & UNLOCK</div></a>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("✅ ICH HABE GETEILT", use_container_width=True):
        st.session_state.full_access = True
        st.success("🎉 Vollzugriff aktiviert!")
        st.rerun()

# --- DASHBOARD & NAVIGATION ---
def render_dashboard_layout():
    with st.sidebar:
        st.markdown("<h1 style='letter-spacing: -1px;'>CREATOR.FANS</h1>", unsafe_allow_html=True)
        st.info("🚀 ALPHA ACCESS: FREE FOREVER")
        page = st.radio("NAVIGATION", ["DASHBOARD", "CHANNELS", "FACTORY", "GALLERY", "CRM", "DEALS", "FINANCE", "PLANNER", "DEMO"])
        
        st.divider()
        if st.button("LOGOUT"):
            st.session_state.authenticated = False
            st.rerun()

    supabase = init_supabase()
    if not supabase:
        st.error("⚠️ Supabase nicht konfiguriert.")
        return

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
        genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
        factory.render_factory(supabase)

def render_dashboard(supabase):
    st.title("ANTIGRAVITY DECK 🚀")
    user_id = "default"
    stats = supabase.table("stats_history").select("*").eq("user_id", user_id).execute()
    
    if not stats.data:
        st.markdown("### 🛠 System Initialization")
        st.info("Willkommen im Terminal. Lade deine ersten Daten.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Option A: Instagram Sync")
            if st.button("📱 Connect Instagram"): st.info("Anleitung folgt.")
        with col2:
            st.markdown("#### Option B: Manual Data Entry")
            with st.expander("Eckdaten eingeben"):
                followers = st.number_input("Follower", value=1000)
                if st.button("Initialize"):
                    supabase.table("stats_history").insert({"platform": "instagram", "metric": "followers", "value": followers, "user_id": user_id}).execute()
                    st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Reach", "125.400", "+8.2%")
        c2.metric("Engagement", "12.300", "-1.5%")
        c3.metric("Followers", "45.120", "+0.4%")

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
    main()
