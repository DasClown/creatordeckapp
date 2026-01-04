-- Supabase Schema für Instagram History Tracking

-- Tabelle erstellen
CREATE TABLE IF NOT EXISTS instagram_history (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    followers INTEGER NOT NULL,
    media_count INTEGER NOT NULL,
    avg_engagement NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index für schnellere Abfragen
CREATE INDEX IF NOT EXISTS idx_instagram_history_date ON instagram_history(date DESC);

-- RLS (Row Level Security) aktivieren
ALTER TABLE instagram_history ENABLE ROW LEVEL SECURITY;

-- Policy: Jeder kann lesen (für anon key)
CREATE POLICY "Allow public read access"
ON instagram_history
FOR SELECT
TO public
USING (true);

-- Policy: Jeder kann einfügen/aktualisieren (für anon key)
CREATE POLICY "Allow public insert/update access"
ON instagram_history
FOR ALL
TO public
USING (true)
WITH CHECK (true);

-- Kommentare
COMMENT ON TABLE instagram_history IS 'Stores daily Instagram account metrics for historical tracking';
COMMENT ON COLUMN instagram_history.date IS 'Date of the snapshot (unique)';
COMMENT ON COLUMN instagram_history.followers IS 'Number of followers on this date';
COMMENT ON COLUMN instagram_history.media_count IS 'Total media count on this date';
COMMENT ON COLUMN instagram_history.avg_engagement IS 'Average engagement (likes + comments) on this date';
