-- Email Logs Tabelle für Tracking von versendeten E-Mails
-- Führe dieses SQL in deinem Supabase SQL Editor aus

CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recipient TEXT NOT NULL,
    subject TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    email_type TEXT DEFAULT 'verification'
);

-- Index für schnellere Abfragen
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient);
CREATE INDEX IF NOT EXISTS idx_email_logs_created_at ON email_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);

-- RLS deaktivieren für Admin-Zugriff
ALTER TABLE email_logs DISABLE ROW LEVEL SECURITY;

-- Optional: Kommentar hinzufügen
COMMENT ON TABLE email_logs IS 'Tracking aller versendeten E-Mails für Debugging und Analytics';
