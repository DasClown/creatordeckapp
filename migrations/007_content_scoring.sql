-- Migration 007: Content Performance Scoring
-- Datum: 2026-01-07
-- Beschreibung: Erstellt View für Top-Performing-Content mit Efficiency-Ranking

-- TOP_PERFORMING_CONTENT View
CREATE OR REPLACE VIEW top_performing_content AS
SELECT 
    va.id,
    va.user_id,
    va.asset_name,
    va.media_type,
    va.platform,
    va.total_revenue,
    va.ppv_opens,
    va.likes,
    va.is_premium,
    -- Conversion Rate (Revenue pro View)
    CASE 
        WHEN va.ppv_opens > 0 THEN va.total_revenue / va.ppv_opens
        ELSE 0
    END as conversion_rate,
    -- Engagement Score
    CASE 
        WHEN va.ppv_opens > 0 THEN (va.likes::DECIMAL / va.ppv_opens) * 100
        ELSE 0
    END as engagement_score,
    -- Efficiency Rank (höchste Conversion Rate = Rank 1)
    ROW_NUMBER() OVER (
        PARTITION BY va.user_id 
        ORDER BY 
            CASE 
                WHEN va.ppv_opens > 0 THEN va.total_revenue / va.ppv_opens
                ELSE 0
            END DESC
    ) as efficiency_rank
FROM vault_assets va
WHERE va.total_revenue > 0 OR va.ppv_opens > 0
ORDER BY conversion_rate DESC;

-- Kommentar
COMMENT ON VIEW top_performing_content IS 'Content-Performance-Analyse mit Conversion-Rate und Efficiency-Ranking';

-- Bestätigung
SELECT 'Migration erfolgreich: Content Performance Scoring View erstellt' AS status;
