-- Migration 004: Revenue Tracking & Vault Analytics
-- Datum: 2026-01-07
-- Beschreibung: Fügt Tabellen für Umsatz-Tracking und Medien-Performance hinzu

-- 1. PROFILES TABELLE REPARIEREN/ERSTELLEN
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    access_level TEXT DEFAULT 'creator',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für schnelle Email-Lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- Kommentar
COMMENT ON TABLE profiles IS 'User-Profile mit Access-Level und Verifizierungs-Status';

-- 2. REVENUE HISTORY (Umsatz-Tracking)
CREATE TABLE IF NOT EXISTS revenue_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL, -- Email-Referenz
    platform TEXT NOT NULL, -- onlyfans, fansly, tiktok, instagram
    amount_gross DECIMAL(10,2), -- Brutto
    amount_net DECIMAL(10,2) NOT NULL, -- Netto (nach Gebühren)
    fee_percentage DECIMAL(5,2) DEFAULT 20.00, -- Platform-Gebühr in %
    source TEXT, -- subscription, tips, ppv, sponsorship
    description TEXT, -- Optionale Beschreibung
    currency TEXT DEFAULT 'EUR',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_rev_user ON revenue_history(user_id);
CREATE INDEX IF NOT EXISTS idx_rev_platform ON revenue_history(platform);
CREATE INDEX IF NOT EXISTS idx_rev_created ON revenue_history(created_at DESC);

-- Kommentar
COMMENT ON TABLE revenue_history IS 'Umsatz-Tracking über alle Plattformen mit Brutto/Netto-Berechnung';

-- 3. VAULT ANALYTICS (Medien-Performance)
CREATE TABLE IF NOT EXISTS vault_assets (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL, -- Email-Referenz
    asset_name TEXT NOT NULL,
    media_type TEXT NOT NULL, -- image, video, audio
    file_size_mb DECIMAL(10,2),
    total_revenue DECIMAL(10,2) DEFAULT 0.00,
    ppv_opens INTEGER DEFAULT 0, -- Pay-Per-View Opens
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    platform TEXT, -- Wo wurde es veröffentlicht
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_vault_user ON vault_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_vault_revenue ON vault_assets(total_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_vault_type ON vault_assets(media_type);

-- Kommentar
COMMENT ON TABLE vault_assets IS 'Medien-Performance-Tracking mit Revenue und Engagement-Metriken';

-- 4. REVENUE SUMMARY VIEW (für schnelle Übersichten)
CREATE OR REPLACE VIEW revenue_summary AS
SELECT 
    user_id,
    platform,
    COUNT(*) as transaction_count,
    SUM(amount_gross) as total_gross,
    SUM(amount_net) as total_net,
    AVG(fee_percentage) as avg_fee,
    MAX(created_at) as last_transaction
FROM revenue_history
GROUP BY user_id, platform;

-- Kommentar
COMMENT ON VIEW revenue_summary IS 'Aggregierte Revenue-Übersicht pro User und Plattform';

-- Bestätigung
SELECT 'Migration erfolgreich: Revenue & Vault Tabellen erstellt' AS status;
