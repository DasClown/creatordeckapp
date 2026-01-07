-- Migration 008: Performance Alert System
-- Datum: 2026-01-07
-- Beschreibung: Erstellt RPC-Funktion für automatische Performance-Alerts

-- RPC-Funktion für Performance-Alerts
CREATE OR REPLACE FUNCTION check_performance_alerts(p_user_id TEXT)
RETURNS TABLE (
    alert_type TEXT,
    message TEXT,
    severity TEXT
) AS $$
BEGIN
    -- Alert 1: Whale Inaktivität (>7 Tage)
    RETURN QUERY
    SELECT 
        'WHALE_INACTIVE'::TEXT as alert_type,
        'Top-Spender inaktiv seit >7 Tagen: ' || COUNT(*)::TEXT || ' Whales benötigen Attention!' as message,
        'HIGH'::TEXT as severity
    FROM (
        SELECT DISTINCT ON (source) 
            source,
            created_at
        FROM revenue_history
        WHERE user_id = p_user_id
        ORDER BY source, created_at DESC
    ) recent
    WHERE created_at < NOW() - INTERVAL '7 days'
    HAVING COUNT(*) > 0;
    
    -- Alert 2: Content-Burnout (Score <20)
    RETURN QUERY
    SELECT 
        'CONTENT_BURNOUT'::TEXT as alert_type,
        'Content-Burnout detected: ' || COUNT(*)::TEXT || ' Assets mit Score <20!' as message,
        'MEDIUM'::TEXT as severity
    FROM top_performing_content
    WHERE user_id = p_user_id
    AND (conversion_rate * 10) < 20
    HAVING COUNT(*) > 0;
    
    -- Alert 3: Revenue-Drop (>20% weniger als letzte Woche)
    RETURN QUERY
    SELECT 
        'REVENUE_DROP'::TEXT as alert_type,
        'Revenue-Drop: Diese Woche ' || ROUND((1 - (this_week / last_week)) * 100)::TEXT || '% weniger als letzte Woche!' as message,
        'HIGH'::TEXT as severity
    FROM (
        SELECT 
            COALESCE(SUM(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN amount_net ELSE 0 END), 0) as this_week,
            COALESCE(SUM(CASE WHEN created_at >= NOW() - INTERVAL '14 days' AND created_at < NOW() - INTERVAL '7 days' THEN amount_net ELSE 0 END), 1) as last_week
        FROM revenue_history
        WHERE user_id = p_user_id
    ) revenue_comparison
    WHERE this_week < (last_week * 0.8) AND last_week > 0;
    
    -- Alert 4: Follower-Drop (negative growth)
    RETURN QUERY
    SELECT 
        'FOLLOWER_DROP'::TEXT as alert_type,
        'Follower-Drop auf ' || platform || ': ' || ABS(net_growth)::TEXT || ' Follower verloren!' as message,
        'MEDIUM'::TEXT as severity
    FROM stats_history
    WHERE user_id = p_user_id
    AND net_growth < 0
    AND created_at >= NOW() - INTERVAL '24 hours'
    ORDER BY created_at DESC
    LIMIT 3;
    
END;
$$ LANGUAGE plpgsql;

-- Kommentar
COMMENT ON FUNCTION check_performance_alerts IS 'Prüft Performance-Metriken und gibt Alerts zurück';

-- Bestätigung
SELECT 'Migration erfolgreich: Performance Alert System erstellt' AS status;
