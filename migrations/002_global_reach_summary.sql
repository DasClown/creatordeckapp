-- Global Reach Summary View/Table
-- Aggregiert Follower-Zahlen über alle Plattformen für einen User

-- Option 1: Als materialized view (empfohlen für Performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS global_reach_summary AS
SELECT 
    user_id,
    SUM(followers) as total_followers,
    COUNT(DISTINCT platform) as platform_count,
    jsonb_agg(
        jsonb_build_object(
            'platform', platform,
            'followers', followers,
            'handle', handle
        ) ORDER BY followers DESC
    ) as platform_breakdown,
    MAX(created_at) as last_updated
FROM stats_history
WHERE followers IS NOT NULL
GROUP BY user_id;

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_global_reach_user ON global_reach_summary(user_id);

-- Refresh-Funktion (manuell oder via Cron)
-- REFRESH MATERIALIZED VIEW global_reach_summary;

-- Option 2: Als normale View (immer aktuell, aber langsamer)
-- CREATE OR REPLACE VIEW global_reach_summary AS
-- ... (gleicher SELECT wie oben)

-- Kommentar
COMMENT ON MATERIALIZED VIEW global_reach_summary IS 'Aggregierte Cross-Platform Reichweiten-Metriken pro User';
