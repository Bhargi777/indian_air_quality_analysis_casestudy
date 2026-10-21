CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- city_daily and station_daily are created from the selected CSV sources by db.py.
-- Indexes are added automatically for date, city, and station filtering.
