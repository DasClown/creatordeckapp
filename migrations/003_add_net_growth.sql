-- Migration: Add net_growth column to stats_history
-- Datum: 2026-01-07
-- Beschreibung: Fügt net_growth Spalte für Follower-Zuwachs-Tracking hinzu

ALTER TABLE stats_history 
ADD COLUMN IF NOT EXISTS net_growth INTEGER DEFAULT 0;

-- Index für Growth-Analysen
CREATE INDEX IF NOT EXISTS idx_stats_history_growth ON stats_history(net_growth DESC) WHERE net_growth IS NOT NULL;

-- Kommentar
COMMENT ON COLUMN stats_history.net_growth IS 'Netto-Follower-Zuwachs seit letztem Sync (positiv/negativ)';

-- Bestätigung
SELECT 'Migration erfolgreich: net_growth Spalte hinzugefügt' AS status;
