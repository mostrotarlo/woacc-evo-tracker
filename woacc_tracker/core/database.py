import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple


class Database:
    def __init__(self, path: str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_schema(self) -> None:
        with self.connect() as db:
            db.executescript(SCHEMA)
            self._ensure_columns(db)
            db.commit()

    def _ensure_columns(self, db: sqlite3.Connection) -> None:
        def cols(table: str) -> set[str]:
            return {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}

        def add(table: str, name: str, ddl: str) -> None:
            if name not in cols(table):
                db.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

        add("session_entries", "potential_lap_ms", "potential_lap_ms INTEGER")
        add("session_entries", "avg_valid_lap_ms", "avg_valid_lap_ms INTEGER")
        add("session_entries", "avg_all_lap_ms", "avg_all_lap_ms INTEGER")
        add("session_entries", "driver_category", "driver_category TEXT")
        add("drivers", "driver_category", "driver_category TEXT")
        add("laps", "invalid_reason", "invalid_reason TEXT")
        add("sessions", "weather_log_at", "weather_log_at TEXT")
        add("sessions", "ambient_temperature_c", "ambient_temperature_c REAL")
        add("sessions", "weather_type", "weather_type TEXT")
        add("sessions", "sky_coverage", "sky_coverage REAL")
        add("sessions", "gloominess", "gloominess REAL")
        add("sessions", "precipitation", "precipitation REAL")
        add("sessions", "fog", "fog REAL")
        add("sessions", "humidity", "humidity REAL")
        add("sessions", "pressure_psi", "pressure_psi REAL")
        add("sessions", "wind_speed_m_s", "wind_speed_m_s REAL")
        add("sessions", "wind_gust", "wind_gust REAL")
        add("sessions", "wind_direction_deg", "wind_direction_deg REAL")
        add("sessions", "initial_global_wetness", "initial_global_wetness REAL")
        add("sessions", "is_dynamic_weather", "is_dynamic_weather INTEGER")
        add("sessions", "initial_grip_label", "initial_grip_label TEXT")
        add("sessions", "track_grip", "track_grip REAL")
        add("sessions", "track_rubber", "track_rubber REAL")
        add("sessions", "track_marbles", "track_marbles REAL")

        add("import_sources", "announce_records", "announce_records INTEGER NOT NULL DEFAULT 0")
        add("import_sources", "announce_name", "announce_name TEXT")
        add("import_sources", "discord_webhook_url", "discord_webhook_url TEXT")
        add("import_sources", "record_window_started_at", "record_window_started_at TEXT")
        add("import_sources", "weekly_recap_enabled", "weekly_recap_enabled INTEGER NOT NULL DEFAULT 0")
        add("import_sources", "weekly_recap_started_at", "weekly_recap_started_at TEXT")
        add("import_sources", "server_log_path", "server_log_path TEXT")

        # Discord/session/license settings (v13.2 social)
        add("import_sources", "session_notify_enabled", "session_notify_enabled INTEGER NOT NULL DEFAULT 0")
        add("import_sources", "session_notify_webhook_url", "session_notify_webhook_url TEXT")
        add("import_sources", "session_notify_mode", "session_notify_mode TEXT")
        add("import_sources", "session_notify_started_at", "session_notify_started_at TEXT")
        add("import_sources", "license_enabled", "license_enabled INTEGER NOT NULL DEFAULT 0")
        add("import_sources", "license_webhook_url", "license_webhook_url TEXT")
        add("import_sources", "license_levels_json", "license_levels_json TEXT")
        add("import_sources", "license_started_at", "license_started_at TEXT")

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        with self.connect() as db:
            cur = db.execute(sql, params)
            db.commit()
            return cur

    def query(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(sql, params).fetchall()

    def one(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(sql, params).fetchone()


SCHEMA = r"""
CREATE TABLE IF NOT EXISTS import_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_scan_at TEXT,
    announce_records INTEGER NOT NULL DEFAULT 0,
    announce_name TEXT,
    discord_webhook_url TEXT,
    record_window_started_at TEXT,
    weekly_recap_enabled INTEGER NOT NULL DEFAULT 0,
    weekly_recap_started_at TEXT,
    server_log_path TEXT,
    session_notify_enabled INTEGER NOT NULL DEFAULT 0,
    session_notify_webhook_url TEXT,
    session_notify_mode TEXT,
    session_notify_started_at TEXT,
    license_enabled INTEGER NOT NULL DEFAULT 0,
    license_webhook_url TEXT,
    license_levels_json TEXT,
    license_started_at TEXT
);

CREATE TABLE IF NOT EXISTS import_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    source_id INTEGER,
    status TEXT NOT NULL,
    reason TEXT,
    imported_at TEXT NOT NULL,
    session_id INTEGER,
    FOREIGN KEY(source_id) REFERENCES import_sources(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_key TEXT NOT NULL UNIQUE,
    server_name TEXT NOT NULL,
    track_name TEXT NOT NULL,
    track_layout TEXT,
    first_session_at TEXT,
    last_session_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    source_id INTEGER,
    file_hash TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    session_name TEXT,
    session_type TEXT NOT NULL,
    session_datetime TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    laps_total INTEGER NOT NULL DEFAULT 0,
    drivers_count INTEGER NOT NULL DEFAULT 0,
    best_lap_ms INTEGER,
    weather_log_at TEXT,
    ambient_temperature_c REAL,
    weather_type TEXT,
    sky_coverage REAL,
    gloominess REAL,
    precipitation REAL,
    fog REAL,
    humidity REAL,
    pressure_psi REAL,
    wind_speed_m_s REAL,
    wind_gust REAL,
    wind_direction_deg REAL,
    initial_global_wetness REAL,
    is_dynamic_weather INTEGER,
    initial_grip_label TEXT,
    track_grip REAL,
    track_rubber REAL,
    track_marbles REAL,
    FOREIGN KEY(server_id) REFERENCES servers(id),
    FOREIGN KEY(source_id) REFERENCES import_sources(id)
);

CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    steam_id TEXT UNIQUE,
    guid_key TEXT,
    display_name TEXT NOT NULL,
    normalized_name TEXT,
    nation TEXT,
    driver_category TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS session_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    driver_guid_key TEXT NOT NULL,
    car_key TEXT NOT NULL,
    car_name TEXT NOT NULL,
    race_number INTEGER,
    driver_category TEXT,
    position INTEGER,
    best_lap_ms INTEGER,
    potential_lap_ms INTEGER,
    avg_valid_lap_ms INTEGER,
    avg_all_lap_ms INTEGER,
    laps_total INTEGER NOT NULL DEFAULT 0,
    laps_valid INTEGER NOT NULL DEFAULT 0,
    gap_ms INTEGER,
    race_total_time_ms INTEGER,
    status TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    UNIQUE(session_id, driver_guid_key, car_key)
);

CREATE TABLE IF NOT EXISTS laps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    lap_number INTEGER NOT NULL,
    lap_time_ms INTEGER NOT NULL,
    is_valid INTEGER NOT NULL DEFAULT 0,
    invalid_reason TEXT,
    flags INTEGER,
    s1_ms INTEGER,
    s2_ms INTEGER,
    s3_ms INTEGER,
    FOREIGN KEY(entry_id) REFERENCES session_entries(id) ON DELETE CASCADE,
    UNIQUE(entry_id, lap_number)
);

CREATE TABLE IF NOT EXISTS record_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    track_name TEXT NOT NULL,
    track_layout TEXT,
    window_started_at TEXT NOT NULL,
    best_lap_ms INTEGER,
    driver_id INTEGER,
    driver_name TEXT,
    car_name TEXT,
    session_id INTEGER,
    lap_id INTEGER,
    updated_at TEXT,
    UNIQUE(source_id, track_name, track_layout, window_started_at),
    FOREIGN KEY(source_id) REFERENCES import_sources(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id),
    FOREIGN KEY(lap_id) REFERENCES laps(id)
);
CREATE TABLE IF NOT EXISTS record_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    track_name TEXT NOT NULL,
    track_layout TEXT,
    window_started_at TEXT NOT NULL,
    lap_ms INTEGER NOT NULL,
    old_lap_ms INTEGER,
    driver_id INTEGER,
    driver_name TEXT,
    car_name TEXT,
    session_id INTEGER,
    lap_id INTEGER,
    session_type TEXT,
    session_datetime TEXT,
    announced_at TEXT NOT NULL,
    discord_status TEXT,
    FOREIGN KEY(source_id) REFERENCES import_sources(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id),
    FOREIGN KEY(lap_id) REFERENCES laps(id)
);


CREATE TABLE IF NOT EXISTS notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_type TEXT NOT NULL,
    source_id INTEGER,
    session_id INTEGER,
    event_key TEXT,
    sent_at TEXT NOT NULL,
    discord_status TEXT,
    UNIQUE(notification_type, source_id, session_id, event_key),
    FOREIGN KEY(source_id) REFERENCES import_sources(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS license_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    steam_id TEXT NOT NULL,
    driver_id INTEGER,
    driver_name TEXT NOT NULL,
    license_name TEXT NOT NULL,
    license_rank INTEGER NOT NULL,
    best_time_ms INTEGER NOT NULL,
    session_id INTEGER,
    achieved_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    discord_status TEXT,
    UNIQUE(source_id, steam_id),
    FOREIGN KEY(source_id) REFERENCES import_sources(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS record_weekly_recaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    records_count INTEGER NOT NULL DEFAULT 0,
    discord_status TEXT,
    FOREIGN KEY(source_id) REFERENCES import_sources(id)
);
"""
