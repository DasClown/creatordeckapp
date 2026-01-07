-- Migration 005: OnlyFans Customer Analytics
-- Datum: 2026-01-07
-- Beschreibung: Fügt Tabelle für OnlyFans-Kunden-Tracking hinzu (Whale Watcher)

-- OF_CUSTOMERS Tabelle (Top Spender / Whale Watcher)
CREATE TABLE IF NOT EXISTS of_customers (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL, -- Creator Email
    customer_username TEXT NOT NULL,
    customer_id TEXT, -- OnlyFans User ID
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    subscription_status TEXT, -- active, expired, cancelled
    last_purchase_date TIMESTAMP WITH TIME ZONE,
    purchase_count INTEGER DEFAULT 0,
    avg_purchase_amount DECIMAL(10,2) DEFAULT 0.00,
    favorite_content_type TEXT, -- ppv, tips, subscription
    notes TEXT, -- Custom notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, customer_username)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_of_customers_user ON of_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_of_customers_spent ON of_customers(total_spent DESC);
CREATE INDEX IF NOT EXISTS idx_of_customers_status ON of_customers(subscription_status);

-- Kommentar
COMMENT ON TABLE of_customers IS 'OnlyFans Kunden-Tracking für Whale-Watcher und Customer-Analytics';

-- OF_SYNC_LOG Tabelle (Sync-History)
CREATE TABLE IF NOT EXISTS of_sync_log (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    sync_type TEXT NOT NULL, -- full, customers, vault, revenue
    status TEXT NOT NULL, -- success, failed, pending
    items_synced INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Index für Sync-Log
CREATE INDEX IF NOT EXISTS idx_of_sync_user ON of_sync_log(user_id);
CREATE INDEX IF NOT EXISTS idx_of_sync_status ON of_sync_log(status);

-- Kommentar
COMMENT ON TABLE of_sync_log IS 'Log für OnlyFans-Synchronisierungen';

-- Whale Watcher View (Top 10 Spender)
CREATE OR REPLACE VIEW whale_watcher AS
SELECT 
    user_id,
    customer_username,
    total_spent,
    subscription_status,
    purchase_count,
    avg_purchase_amount,
    last_purchase_date,
    CASE 
        WHEN total_spent >= 1000 THEN 'WHALE'
        WHEN total_spent >= 500 THEN 'DOLPHIN'
        WHEN total_spent >= 100 THEN 'FISH'
        ELSE 'MINNOW'
    END as customer_tier
FROM of_customers
ORDER BY total_spent DESC;

-- Kommentar
COMMENT ON VIEW whale_watcher IS 'Top-Spender-Übersicht mit Tier-Klassifizierung';

-- Bestätigung
SELECT 'Migration erfolgreich: OnlyFans Customer Analytics erstellt' AS status;
