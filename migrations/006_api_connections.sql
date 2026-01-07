-- Migration 006: API Connections für sichere Token-Speicherung
-- Datum: 2026-01-07
-- Beschreibung: Fügt Tabelle für API-Tokens (Fansly, OnlyFans, etc.) hinzu

-- API_CONNECTIONS Tabelle (sichere Token-Speicherung)
CREATE TABLE IF NOT EXISTS api_connections (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL, -- Creator Email
    platform TEXT NOT NULL, -- fansly, onlyfans, tiktok, etc.
    api_token TEXT NOT NULL, -- Encrypted Token
    token_type TEXT DEFAULT 'bearer', -- bearer, binding, oauth
    refresh_token TEXT, -- Falls OAuth
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, platform)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_api_conn_user ON api_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_api_conn_platform ON api_connections(platform);
CREATE INDEX IF NOT EXISTS idx_api_conn_active ON api_connections(is_active) WHERE is_active = TRUE;

-- Kommentar
COMMENT ON TABLE api_connections IS 'Sichere Speicherung von API-Tokens für Platform-Integrationen';

-- RLS deaktivieren (nur für Admin-Zugriff)
ALTER TABLE api_connections DISABLE ROW LEVEL SECURITY;

-- Bestätigung
SELECT 'Migration erfolgreich: API Connections Tabelle erstellt' AS status;
