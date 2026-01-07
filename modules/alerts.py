"""
PERFORMANCE ALERT SYSTEM
Automatische Email-Benachrichtigungen für kritische Events
"""

import streamlit as st
import resend

def send_performance_alert(alert_type, message, severity="MEDIUM"):
    """
    Sendet Performance-Alert via Resend Email.
    
    Args:
        alert_type: Art des Alerts (z.B. WHALE_INACTIVE)
        message: Alert-Nachricht
        severity: HIGH, MEDIUM, LOW
    
    Returns:
        bool: True bei Erfolg
    """
    try:
        # Resend API Key aus Secrets
        resend.api_key = st.secrets.get("RESEND_API_KEY", "")
        
        if not resend.api_key:
            st.warning("⚠️ RESEND_API_KEY nicht konfiguriert. Alerts werden nicht versendet.")
            return False
        
        user_email = st.session_state.get('user_email', 'unknown')
        
        # Severity-Emoji
        severity_emoji = {
            "HIGH": "🚨",
            "MEDIUM": "⚠️",
            "LOW": "ℹ️"
        }
        emoji = severity_emoji.get(severity, "📊")
        
        # Email-Parameter
        params = {
            "from": "Content Core <alerts@content-core.com>",
            "to": [user_email],
            "subject": f"{emoji} PERFORMANCE ALERT: {alert_type.replace('_', ' ')}",
            "html": f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #1f1f1f;">{emoji} System-Meldung</h2>
                    <p style="font-size: 16px; color: #333;">{message}</p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 14px; color: #666;">
                        <strong>Severity:</strong> {severity}<br>
                        <strong>Alert Type:</strong> {alert_type}
                    </p>
                    <a href="https://content-core.com" 
                       style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                        Dashboard prüfen
                    </a>
                    <p style="font-size: 12px; color: #999; margin-top: 30px;">
                        Content Core Performance Alert System
                    </p>
                </body>
            </html>
            """,
        }
        
        resend.Emails.send(params)
        return True
        
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

def run_alert_engine(supabase):
    """
    Führt Alert-Engine aus und versendet Benachrichtigungen.
    
    Prüft Performance-Metriken via RPC und sendet Alerts bei kritischen Events.
    """
    try:
        user_email = st.session_state.get('user_email', 'unknown')
        
        # RPC-Call für Performance-Alerts
        alerts = supabase.rpc('check_performance_alerts', {'p_user_id': user_email}).execute()
        
        if alerts.data and len(alerts.data) > 0:
            # Alerts verarbeiten
            for alert in alerts.data:
                alert_type = alert.get('alert_type', 'UNKNOWN')
                message = alert.get('message', 'No message')
                severity = alert.get('severity', 'MEDIUM')
                
                # Email senden
                send_performance_alert(alert_type, message, severity)
            
            return len(alerts.data)
        
        return 0
        
    except Exception as e:
        # Silent fail - Alert-Engine soll App nicht crashen
        print(f"Alert Engine Error: {e}")
        return 0

def display_alert_dashboard(supabase):
    """Rendert Alert-Dashboard mit manueller Trigger-Option."""
    st.title("🚨 PERFORMANCE ALERTS")
    
    user_email = st.session_state.get('user_email', 'unknown')
    
    st.info("""
    **Automatisches Alert-System**
    
    Das System prüft automatisch:
    - 🐋 Whale-Inaktivität (>7 Tage)
    - 🔥 Content-Burnout (Score <20)
    - 💰 Revenue-Drops (>20% weniger)
    - 📉 Follower-Drops (negative Growth)
    """)
    
    # Manuelle Prüfung
    if st.button("🔍 JETZT PRÜFEN", use_container_width=True):
        with st.spinner("Prüfe Performance-Metriken..."):
            try:
                alerts = supabase.rpc('check_performance_alerts', {'p_user_id': user_email}).execute()
                
                if alerts.data and len(alerts.data) > 0:
                    st.warning(f"⚠️ {len(alerts.data)} Alert(s) gefunden!")
                    
                    for alert in alerts.data:
                        alert_type = alert.get('alert_type', 'UNKNOWN')
                        message = alert.get('message', 'No message')
                        severity = alert.get('severity', 'MEDIUM')
                        
                        # Display Alert
                        if severity == "HIGH":
                            st.error(f"🚨 **{alert_type}**: {message}")
                        elif severity == "MEDIUM":
                            st.warning(f"⚠️ **{alert_type}**: {message}")
                        else:
                            st.info(f"ℹ️ **{alert_type}**: {message}")
                    
                    # Email-Option
                    if st.button("📧 ALERTS PER EMAIL SENDEN"):
                        sent_count = 0
                        for alert in alerts.data:
                            if send_performance_alert(
                                alert.get('alert_type'),
                                alert.get('message'),
                                alert.get('severity')
                            ):
                                sent_count += 1
                        
                        if sent_count > 0:
                            st.success(f"✅ {sent_count} Alert(s) per Email versendet!")
                        else:
                            st.error("❌ Email-Versand fehlgeschlagen")
                else:
                    st.success("✅ Keine Alerts! Alles läuft optimal.")
                    
            except Exception as e:
                st.error(f"Alert Check Error: {e}")
                st.info("💡 Stelle sicher, dass Migration 008 ausgeführt wurde: `migrations/008_performance_alerts.sql`")
    
    # Alert-History (optional)
    st.markdown("---")
    st.markdown("### 📜 ALERT-KONFIGURATION")
    
    with st.expander("⚙️ ALERT-SCHWELLWERTE"):
        st.markdown("""
        **Aktuelle Schwellwerte:**
        
        - **Whale-Inaktivität:** >7 Tage
        - **Content-Burnout:** Score <20
        - **Revenue-Drop:** >20% weniger als Vorwoche
        - **Follower-Drop:** Negative Growth in letzten 24h
        
        *Schwellwerte können in `migrations/008_performance_alerts.sql` angepasst werden.*
        """)
