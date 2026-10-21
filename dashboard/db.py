from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("AIR_QUALITY_DATA_DIR", str(PROJECT_DIR)))
DB_PATH = Path(os.getenv("AIR_QUALITY_DB_PATH", str(Path(__file__).resolve().parent / "data" / "air_quality.sqlite")))

CITY_CANDIDATES = ("powerbi_city_daily.csv", "city_day_clean.csv", "city_day.csv")
STATION_CANDIDATES = ("powerbi_station_daily.csv", "station_day_clean.csv", "station_day.csv")
STATION_LOOKUP = "stations.csv"
POLLUTANTS = ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene"]

REGIONS = {
    "North": ["Delhi", "Gurugram", "Chandigarh", "Amritsar", "Jaipur", "Lucknow"],
    "South": ["Bengaluru", "Chennai", "Hyderabad", "Amaravati", "Visakhapatnam", "Coimbatore", "Thiruvananthapuram", "Ernakulam", "Kochi"],
    "East": ["Kolkata", "Patna", "Jorapokhar", "Brajrajnagar", "Talcher"],
    "West": ["Ahmedabad", "Mumbai"],
    "Central": ["Bhopal"],
    "North-East": ["Guwahati", "Shillong", "Aizawl"],
}
CITY_REGION = {city: region for region, cities in REGIONS.items() for city in cities}
SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Summer", 4: "Summer", 5: "Summer",
    6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Post-Monsoon", 11: "Post-Monsoon",
}


def _pick_file(candidates: tuple[str, ...]) -> Path:
    for name in candidates:
        path = DATA_DIR / name
        if path.exists():
            return path
    expected = ", ".join(candidates)
    raise FileNotFoundError(f"Could not find any of [{expected}] in {DATA_DIR}")


def _read_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    return frame


def _prepare_city(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "Date" not in frame or "AQI" not in frame or "City" not in frame:
        raise ValueError("City data must contain City, Date, and AQI columns.")
    frame["AQI"] = pd.to_numeric(frame["AQI"], errors="coerce")
    if "Month" not in frame.columns:
        frame["Month"] = frame["Date"].dt.month
    if "Year" not in frame.columns:
        frame["Year"] = frame["Date"].dt.year
    if "Season" not in frame.columns:
        frame["Season"] = frame["Month"].map(SEASON_BY_MONTH)
    if "Region" not in frame.columns:
        frame["Region"] = frame["City"].map(CITY_REGION).fillna("Unknown")
    if "AQI_Bucket" not in frame.columns:
        frame["AQI_Bucket"] = pd.cut(
            frame["AQI"],
            bins=[float("-inf"), 50, 100, 200, 300, 400, float("inf")],
            labels=["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"],
        ).astype("string")
    return frame.dropna(subset=["City", "Date", "AQI"])


def _prepare_station(frame: pd.DataFrame, lookup_path: Path | None) -> pd.DataFrame:
    frame = frame.copy()
    if lookup_path and lookup_path.exists() and "StationId" in frame.columns:
        lookup = _read_csv(lookup_path)
        if "StationId" in lookup.columns:
            missing_fields = [c for c in ("StationName", "City", "State", "Status") if c in lookup.columns and c not in frame.columns]
            if missing_fields:
                frame = frame.merge(lookup[["StationId"] + missing_fields].drop_duplicates("StationId"), on="StationId", how="left")
    if "Date" not in frame or "AQI" not in frame:
        raise ValueError("Station data must contain Date and AQI columns.")
    frame["AQI"] = pd.to_numeric(frame["AQI"], errors="coerce")
    if "Year" not in frame.columns:
        frame["Year"] = frame["Date"].dt.year
    return frame.dropna(subset=["Date", "AQI"])


def _manifest(city_path: Path, station_path: Path, lookup_path: Path | None) -> str:
    paths = [city_path, station_path]
    if lookup_path and lookup_path.exists():
        paths.append(lookup_path)
    return "|".join(f"{p.resolve()}:{p.stat().st_size}:{p.stat().st_mtime_ns}" for p in paths)


def initialize_database() -> dict[str, object]:
    """Create/update the local SQLite database when its CSV sources change."""
    city_path = _pick_file(CITY_CANDIDATES)
    station_path = _pick_file(STATION_CANDIDATES)
    lookup_path = DATA_DIR / STATION_LOOKUP
    signature = _manifest(city_path, station_path, lookup_path)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        prior = connection.execute("SELECT value FROM app_metadata WHERE key='source_signature'").fetchone()
        existing = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('city_daily','station_daily')").fetchall()
        if prior and prior[0] == signature and len(existing) == 2:
            return {"database": DB_PATH, "city_source": city_path, "station_source": station_path, "reloaded": False}

        city = _prepare_city(_read_csv(city_path))
        station = _prepare_station(_read_csv(station_path), lookup_path if lookup_path.exists() else None)
        city.to_sql("city_daily", connection, if_exists="replace", index=False)
        station.to_sql("station_daily", connection, if_exists="replace", index=False)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_city_date ON city_daily(Date)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_city_name ON city_daily(City)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_station_date ON station_daily(Date)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_station_city ON station_daily(City)")
        connection.execute(
            "INSERT INTO app_metadata(key, value) VALUES('source_signature', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (signature,)
        )
        connection.execute(
            "INSERT INTO app_metadata(key, value) VALUES('city_source', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (city_path.name,)
        )
        connection.execute(
            "INSERT INTO app_metadata(key, value) VALUES('station_source', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (station_path.name,)
        )
        return {"database": DB_PATH, "city_source": city_path, "station_source": station_path, "reloaded": True}


def read_table(table_name: str) -> pd.DataFrame:
    """Read an allowed dashboard table from SQLite."""
    if table_name not in {"city_daily", "station_daily"}:
        raise ValueError("Unsupported table name")
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(f'SELECT * FROM "{table_name}"', connection, parse_dates=["Date"])


def row_counts() -> tuple[int, int]:
    with sqlite3.connect(DB_PATH) as connection:
        city_count = connection.execute("SELECT COUNT(*) FROM city_daily").fetchone()[0]
        station_count = connection.execute("SELECT COUNT(*) FROM station_daily").fetchone()[0]
    return int(city_count), int(station_count)
