import streamlit as st
import toml
import os

# Module importieren
from modules import crm, finance, planner, factory, gallery, channels, deals, demo
import pandas as pd
import google.generativeai as genai
from supabase import create_client

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

# --- SETUP ---
st.set_page_config(
    page_title="CREATOR.FANS",
    page_icon="🚀",
    layout="wide"
)

# --- ANALYTICS ---
st.markdown("""
    <script src="https://cdn.usefathom.com/script.js" data-site="YOUR_ID" defer></script>
""", unsafe_allow_html=True)

# --- SEO & META TAGS ---
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

# --- CSS STYLING (RADICAL MINIMALISM) ---
st.markdown("""
<style>
    /* Google Font: Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Radikaler Minimalismus: Keine Schatten, nur 1px Linien */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E0E0E0 !important;
    }

    /* Card-Ersatz: Flache Boxen */
    .stMetric, .ai-box, .custom-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 0px !important; /* Harte Kanten für edlen Look */
        padding: 20px !important;
        box-shadow: none !important;
    }

    /* Buttons: Black & White */
    .stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 0px !important;
        border: 1px solid #000000 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 0px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: #FFFFFF !important;
    }

    /* Metriken */
    [data-testid="stMetricValue"] {
        font-weight: 300 !important;
        letter-spacing: -1px;
        font-size: 2.5rem !important;
        color: #000000 !important;
    }
    
    /* Akzentuierte Metriken */
    [data-testid="stMetricDelta"] > div {
        font-weight: 500 !important;
    }

    /* Erfolg/Einnahmen (Grün) */
    div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaDirection-Up"] {
        color: #28a745 !important;
    }

    /* Verlust/Ausgaben (Rot) */
    div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaDirection-Down"] {
        color: #dc3545 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        color: #888888;
    }
    .stTabs [aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 2px solid #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LANDING PAGE ---
def render_landing_page():
    st.markdown("""
        <div style='padding: 80px 20px; text-align: center;'>
            <h1 style='font-size: 64px; font-weight: 300; letter-spacing: -2px;'>CREATOR.FANS</h1>
            <p style='font-size: 18px; color: #666; font-weight: 300; max-width: 600px; margin: 0 auto 40px auto;'>
                Advanced Analytics. Zero Cost. High Impact. <br>
                🚀 Alpha Access: Free Forever für Early Adopters
            </p>
        </div>
    """, unsafe_allow_html=True)

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
                        # Check if email already exists
                        existing = supabase.table("waitlist").select("email").eq("email", email).execute()
                        if existing.data and len(existing.data) > 0:
                            st.info("ℹ️ Du bist bereits auf der Warteliste!")
                        else:
                            supabase.table("waitlist").insert({"email": email}).execute()
                            st.success("✅ Auf die Warteliste gesetzt.")
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

# --- VIEW MANAGEMENT ---
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

# Landing Page
if st.session_state.view == "landing":
    render_landing_page()
    st.stop()

# Login Check
if not st.session_state.password_correct:
    pwd = st.text_input("Access Code", type="password")
    if st.button("UNLOCK"):
        if pwd == st.secrets.get("APP_PASSWORD", "Start123!"):
            st.session_state.password_correct = True
            st.rerun()
    st.stop()

# --- VIRAL SHARE-TO-UNLOCK ---
if "full_access" not in st.session_state:
    st.session_state.full_access = False

if not st.session_state.full_access:
    st.markdown("""
        <div style='padding: 60px 20px; text-align: center;'>
            <h2 style='font-weight: 300; margin-bottom: 20px;'>🔓 ACTIVATE FULL ENGINE</h2>
            <p style='color: #666; margin-bottom: 30px; font-weight: 300;'>
                Teile CREATOR.FANS auf Social Media und erhalte sofortigen Vollzugriff.<br>
                Kostenlos. Für immer.
            </p>
            <div style='background: #ffffff; padding: 0px; margin: 40px auto; max-width: 600px; text-align: center;'>
                <p style='margin: 0; font-size: 16px; color: #000000; font-weight: 300;'>
                    🔒 <span style='font-weight: 600;'>Privacy First:</span> Deine Daten bleiben verschlüsselt in deiner Supabase-Instanz. 
                    Zero-Knowledge Architecture.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🐦 TWITTER/X")
        share_twitter = "https://twitter.com/intent/tweet?text=Gerade%20das%20neue%20Terminal%20von%20creator.fans%20entdeckt.%20Endlich%20Ordnung%20im%20Workflow.%20%F0%9F%94%A5"
        st.markdown(f"""
            <a href='{share_twitter}' target='_blank' style='text-decoration:none;'>
                <div style='padding:15px; border:1px solid #000; color:#000; text-align:center; background:#fff; transition: all 0.3s;'>
                    TWEET & UNLOCK
                </div>
            </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🔴 REDDIT")
        share_reddit = "https://www.reddit.com/submit?title=CREATOR.FANS%20-%20Advanced%20Analytics%20for%20Creators&url=https://creator.fans"
        st.markdown(f"""
            <a href='{share_reddit}' target='_blank' style='text-decoration:none;'>
                <div style='padding:15px; border:1px solid #000; color:#000; text-align:center; background:#fff; transition: all 0.3s;'>
                    POST & UNLOCK
                </div>
            </a>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("<p style='text-align: center; color: #999; font-size: 14px;'>Nach dem Posten klicke hier:</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("✅ ICH HABE GETEILT", use_container_width=True):
            st.session_state.full_access = True
            st.success("🎉 Vollzugriff aktiviert! Danke fürs Teilen!")
            st.rerun()
    
    st.stop()

# --- NAVIGATION ---
CREATOR_DISPLAY_NAME = st.secrets.get("BRAND_NAME", "Admin")

with st.sidebar:
    st.markdown("<h1 style='letter-spacing: -1px;'>CREATOR.FANS</h1>", unsafe_allow_html=True)
    st.info("🚀 ALPHA ACCESS: FREE FOREVER FOR EARLY ADOPTERS")
    page = st.radio("NAVIGATION", [
        "DASHBOARD", "CHANNELS", "FACTORY", "GALLERY", "CRM", "DEALS", "FINANCE", "PLANNER", "DEMO"
    ])
    
    with st.expander("⚙️ SETTINGS"):
        st.caption(f"Connected: {CREATOR_DISPLAY_NAME}")
        if st.button("Sync APIs"):
            st.rerun()
        st.color_picker("Brand Color", "#ffffff")
    
    # Help & Support Section
    st.markdown("---")
    st.markdown("### 📟 Support & Docs")
    st.caption("Lerne, wie du deine Daten korrekt exportierst und hier importierst.")
    
    if st.button("📺 Video Tutorial", use_container_width=True):
        st.info("Tutorial-Video wird in Kürze verfügbar sein!")
    
    if st.button("📖 Documentation", use_container_width=True):
        st.info("Dokumentation wird in Kürze verfügbar sein!")
    
    st.caption("💬 Support: contact@creator.fans")
    
    st.divider()
    if st.button("LOGOUT"):
        st.session_state.password_correct = False
        st.rerun()

# --- DEMO DATA (für Factory) ---
def get_demo_data():
    return pd.DataFrame({
        'Caption': ['Top Post 1', 'Top Post 2', 'Top Post 3'],
        'Engagement': [450, 380, 320]
    })

# --- SUPABASE INIT ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

# --- ROUTING ---
if page == "DASHBOARD":
    st.title("ANTIGRAVITY DECK 🚀")
    
    # Supabase initialisieren
    supabase = init_supabase()
    
    if supabase:
        # Prüfe auf vorhandene Daten (user_id = "default" für Single-User)
        user_id = "default"
        stats = supabase.table("stats_history").select("*").eq("user_id", user_id).execute()
        
        if not stats.data or len(stats.data) == 0:
            # Onboarding Wizard
            st.markdown("### 🛠 System Initialization")
            st.info("Willkommen im Terminal. Um die Analyse-Engine zu starten, benötigen wir die ersten Datenpunkte.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Option A: Instagram Sync")
                st.caption("Verbinde dein Instagram-Konto für automatische Daten-Updates.")
                if st.button("📱 Connect Instagram", use_container_width=True):
                    st.info("📖 Anleitung: Gehe zu Settings → Help & Docs für das Setup-Tutorial")
                    st.session_state.setup_step = "ig_sync"
                    
            with col2:
                st.markdown("#### Option B: Manual Data Entry")
                st.caption("Starte mit manuellen Daten und synchronisiere später.")
                with st.expander("Eckdaten manuell eingeben"):
                    followers = st.number_input("Follower Anzahl", min_value=0, value=1000)
                    avg_likes = st.number_input("Ø Likes pro Post", min_value=0, value=100)
                    if st.button("Initialize with Manual Data"):
                        try:
                            supabase.table("stats_history").insert({
                                "platform": "instagram",
                                "metric": "followers",
                                "value": followers,
                                "user_id": user_id
                            }).execute()
                            supabase.table("stats_history").insert({
                                "platform": "instagram",
                                "metric": "avg_likes",
                                "value": avg_likes,
                                "user_id": user_id
                            }).execute()
                            st.success("✅ Daten initialisiert! Lade neu...")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Speichern: {e}")
        else:
            # Main Dashboard mit Metriken
            c1, c2, c3 = st.columns(3)
            c1.metric("Reach", "125.400", "+8.2%")
            c2.metric("Engagement", "12.300", "-1.5%")
            c3.metric("Followers", "45.120", "+0.4%")
            
            # Critical Alerts System
            from datetime import datetime, timedelta
            
            st.divider()
            st.subheader("⚠️ CRITICAL ALERTS")
            
            try:
                threshold = datetime.now() + timedelta(hours=48)
                res_deals = supabase.table("deals").select("*").lte("deadline", str(threshold.date())).eq("status", "Closed").execute()
                res_plan = supabase.table("content_plan").select("title, platform").execute()
                planned_titles = [item['title'] for item in res_plan.data] if res_plan.data else []

                alerts_found = False
                for deal in res_deals.data if res_deals.data else []:
                    if deal['brand'] not in str(planned_titles):
                        st.error(f"**MISSING ASSET:** Für den Deal mit '{deal['brand']}' (Fällig: {deal['deadline']}) wurde noch kein Content geplant!")
                        alerts_found = True
                        
                if not alerts_found:
                    st.success("✅ Alle fälligen Deals sind im Zeitplan. Keine kritischen Warnungen.")
            except Exception as e:
                st.warning(f"Alerts konnten nicht geladen werden: {e}")
    else:
        st.error("⚠️ Supabase nicht konfiguriert.")
    
    st.info("💡 Dashboard-Logik wird hier integriert (Instagram API, Analytics, etc.)")

elif page == "GALLERY":
    supabase = init_supabase()
    if supabase:
        gallery.render_gallery(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Gallery benötigt Cloud Storage.")

elif page == "CHANNELS":
    channels.render_channels()

elif page == "DEALS":
    deals.render_deals()

elif page == "CRM":
    supabase = init_supabase()
    if supabase:
        crm.render_crm(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Bitte SUPABASE_URL und SUPABASE_KEY in secrets.toml hinzufügen.")

elif page == "FINANCE":
    supabase = init_supabase()
    if supabase:
        finance.render_finance(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Bitte SUPABASE_URL und SUPABASE_KEY in secrets.toml hinzufügen.")

elif page == "PLANNER":
    supabase = init_supabase()
    if supabase:
        planner.render_planner(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Bitte SUPABASE_URL und SUPABASE_KEY in secrets.toml hinzufügen.")

elif page == "DEMO":
    demo.render_demo()

elif page == "FACTORY":
    # Gemini API konfigurieren
    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
    
    # Supabase für Performance-Daten
    supabase = init_supabase()
    if supabase:
        factory.render_factory(supabase)
    else:
        st.error("⚠️ Supabase nicht konfiguriert. Factory benötigt Zugriff auf Performance-Daten.")
