-- Migration: Erweitere stats_history Tabelle um zusätzliche Metriken
-- Datum: 2026-01-07
-- Beschreibung: Fügt video_views, total_likes und subscriber_count hinzu

-- Führe dieses SQL in deinem Supabase SQL Editor aus

ALTER TABLE stats_history 
ADD COLUMN IF NOT EXISTS video_views BIGINT,
ADD COLUMN IF NOT EXISTS total_likes BIGINT,
ADD COLUMN IF NOT EXISTS subscriber_count INTEGER;

-- Optional: Kommentare hinzufügen für Dokumentation
COMMENT ON COLUMN stats_history.video_views IS 'Gesamtanzahl Video-Aufrufe (YouTube, TikTok, etc.)';
COMMENT ON COLUMN stats_history.total_likes IS 'Gesamtanzahl Likes über alle Posts';
COMMENT ON COLUMN stats_history.subscriber_count IS 'Anzahl Abonnenten/Subscriber (YouTube, Newsletter, etc.)';

-- Bestätigung
SELECT 'Migration erfolgreich: stats_history erweitert' AS status;
