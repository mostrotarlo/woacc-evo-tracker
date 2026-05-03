from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from .database import Database
from .parser import parse_evo_results, file_sha256
from .records_discord import post_discord_record, post_discord_weekly_recap
from .utils import normalize_text


class Importer:
    def __init__(self, db: Database, log=print):
        self.db = db
        self.log = log
        self.db.init_schema()
        self.pending_record_candidates = {}

    def ensure_source(self, folder: Path, name: str, source_cfg: Optional[Dict] = None) -> int:
        source_cfg = source_cfg or {}
        folder = folder.resolve()

        row = self.db.one("SELECT id FROM import_sources WHERE path=?", (str(folder),))
        now = datetime.now().isoformat(timespec="seconds")

        announce_records = 1 if source_cfg.get("announce_records") else 0
        announce_name = source_cfg.get("announce_name") or name
        webhook = (source_cfg.get("discord_webhook_url") or "").strip()
        window = source_cfg.get("record_window_started_at") or None

        weekly_recap_enabled = 1 if source_cfg.get("weekly_recap_enabled") else 0
        weekly_recap_started_at = source_cfg.get("weekly_recap_started_at") or None

        if row:
            self.db.execute(
                """UPDATE import_sources
                   SET name=?,
                       enabled=1,
                       last_scan_at=?,
                       announce_records=?,
                       announce_name=?,
                       discord_webhook_url=?,
                       record_window_started_at=?,
                       weekly_recap_enabled=?,
                       weekly_recap_started_at=?
                   WHERE id=?""",
                (
                    name,
                    now,
                    announce_records,
                    announce_name,
                    webhook,
                    window,
                    weekly_recap_enabled,
                    weekly_recap_started_at,
                    row["id"],
                ),
            )
            return int(row["id"])

        cur = self.db.execute(
            """INSERT INTO import_sources(
                name,
                path,
                enabled,
                last_scan_at,
                announce_records,
                announce_name,
                discord_webhook_url,
                record_window_started_at,
                weekly_recap_enabled,
                weekly_recap_started_at
            )
            VALUES(?,?,1,?,?,?,?,?,?,?)""",
            (
                name,
                str(folder),
                now,
                announce_records,
                announce_name,
                webhook,
                window,
                weekly_recap_enabled,
                weekly_recap_started_at,
            ),
        )
        return int(cur.lastrowid)

    def import_folder(self, folder: Path, source_name: Optional[str] = None, source_cfg: Optional[Dict] = None) -> Dict[str, int]:
        folder = Path(folder)
        stats = {"found": 0, "imported": 0, "skipped": 0, "errors": 0}

        if not folder.exists() or not folder.is_dir():
            return stats

        source_id = self.ensure_source(folder, source_name or folder.name, source_cfg)

        for path in sorted(folder.glob("*.json")):
            stats["found"] += 1
            result = self.import_file(path, source_id)

            if result == "imported":
                stats["imported"] += 1
            elif result == "error":
                stats["errors"] += 1
            else:
                stats["skipped"] += 1

        self.db.execute(
            "UPDATE import_sources SET last_scan_at=? WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), source_id),
        )

        return stats

    def import_file(self, path: Path, source_id: Optional[int] = None) -> str:
        path = Path(path)
        now = datetime.now().isoformat(timespec="seconds")

        try:
            fhash = file_sha256(path)

            existing = self.db.one("SELECT status FROM import_files WHERE file_hash=?", (fhash,))
            if existing:
                return "skipped"

            parsed = parse_evo_results(path)

            if int(parsed.get("laps_total") or 0) <= 0:
                self.db.execute(
                    "INSERT OR IGNORE INTO import_files(file_path,file_hash,source_id,status,reason,imported_at) VALUES(?,?,?,?,?,?)",
                    (str(path), fhash, source_id, "skipped", "Sessione senza giri", now),
                )
                return "skipped"

            session_id = self._save_parsed(parsed, source_id)

            self.db.execute(
                "INSERT OR IGNORE INTO import_files(file_path,file_hash,source_id,status,reason,imported_at,session_id) VALUES(?,?,?,?,?,?,?)",
                (str(path), fhash, source_id, "imported", "", now, session_id),
            )

            self._check_and_announce_records(source_id, parsed, session_id)

            return "imported"

        except Exception as exc:
            try:
                fhash = file_sha256(path)
            except Exception:
                fhash = f"error:{path}:{now}"

            self.db.execute(
                "INSERT OR IGNORE INTO import_files(file_path,file_hash,source_id,status,reason,imported_at) VALUES(?,?,?,?,?,?)",
                (str(path), fhash, source_id, "error", str(exc), now),
            )

            return "error"

    def _save_parsed(self, parsed: Dict, source_id: Optional[int]) -> int:
        server = self.db.one(
            "SELECT id, first_session_at, last_session_at FROM servers WHERE server_key=?",
            (parsed["server_key"],),
        )

        if server:
            server_id = int(server["id"])
            first = min(filter(None, [server["first_session_at"], parsed["session_datetime"]]))
            last = max(filter(None, [server["last_session_at"], parsed["session_datetime"]]))

            self.db.execute(
                "UPDATE servers SET server_name=?, track_name=?, track_layout=?, first_session_at=?, last_session_at=? WHERE id=?",
                (
                    parsed["server_name"],
                    parsed["track_name"],
                    parsed.get("track_layout"),
                    first,
                    last,
                    server_id,
                ),
            )

        else:
            cur = self.db.execute(
                "INSERT INTO servers(server_key,server_name,track_name,track_layout,first_session_at,last_session_at) VALUES(?,?,?,?,?,?)",
                (
                    parsed["server_key"],
                    parsed["server_name"],
                    parsed["track_name"],
                    parsed.get("track_layout"),
                    parsed["session_datetime"],
                    parsed["session_datetime"],
                ),
            )
            server_id = int(cur.lastrowid)

        cur = self.db.execute(
            """INSERT INTO sessions(
                server_id,
                source_id,
                file_hash,
                file_path,
                session_name,
                session_type,
                session_datetime,
                is_completed,
                laps_total,
                drivers_count,
                best_lap_ms
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                server_id,
                source_id,
                parsed["file_hash"],
                parsed["file_path"],
                parsed.get("session_name"),
                parsed["session_type"],
                parsed["session_datetime"],
                1 if parsed.get("is_completed") else 0,
                parsed.get("laps_total") or 0,
                parsed.get("drivers_count") or 0,
                parsed.get("best_lap_ms"),
            ),
        )
        session_id = int(cur.lastrowid)

        for entry in parsed.get("entries", []):
            driver_id = self._upsert_driver(entry, parsed["session_datetime"])

            cur = self.db.execute(
                """INSERT INTO session_entries(
                    session_id,
                    driver_id,
                    driver_guid_key,
                    car_key,
                    car_name,
                    race_number,
                    driver_category,
                    position,
                    best_lap_ms,
                    potential_lap_ms,
                    avg_valid_lap_ms,
                    avg_all_lap_ms,
                    laps_total,
                    laps_valid,
                    gap_ms,
                    race_total_time_ms,
                    status
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    session_id,
                    driver_id,
                    entry["driver_key"],
                    entry["car_key"],
                    entry.get("car_name") or "Unknown car",
                    entry.get("race_number"),
                    entry.get("driver_category") or "",
                    entry.get("position"),
                    entry.get("best_lap_ms"),
                    entry.get("potential_lap_ms"),
                    entry.get("avg_valid_lap_ms"),
                    entry.get("avg_all_lap_ms"),
                    entry.get("laps_total") or 0,
                    entry.get("laps_valid") or 0,
                    entry.get("gap_ms"),
                    entry.get("race_total_time_ms"),
                    entry.get("status"),
                ),
            )
            entry_id = int(cur.lastrowid)

            for lap in entry.get("laps", []):
                self.db.execute(
                    """INSERT INTO laps(
                        entry_id,
                        lap_number,
                        lap_time_ms,
                        is_valid,
                        flags,
                        s1_ms,
                        s2_ms,
                        s3_ms
                    )
                    VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        entry_id,
                        lap["lap_number"],
                        lap["lap_time_ms"],
                        1 if lap.get("is_valid") else 0,
                        lap.get("flags"),
                        lap.get("s1_ms"),
                        lap.get("s2_ms"),
                        lap.get("s3_ms"),
                    ),
                )

        return session_id

    def _check_and_announce_records(self, source_id: Optional[int], parsed: Dict, session_id: int) -> None:
        if not source_id:
            return

        src = self.db.one("SELECT * FROM import_sources WHERE id=?", (source_id,))
        if not src or not src["announce_records"] or not src["record_window_started_at"]:
            return

        if not src["discord_webhook_url"]:
            self.log(f"Record skip: webhook mancante per {src['name']}")
            return

        window = src["record_window_started_at"]
        track = parsed.get("track_name") or "Unknown track"
        layout = parsed.get("track_layout") or ""

        candidates = self.db.query(
            """SELECT l.id AS lap_id,
                      l.lap_time_ms,
                      se.car_name,
                      d.id AS driver_id,
                      d.display_name
               FROM laps l
               JOIN session_entries se ON se.id=l.entry_id
               JOIN drivers d ON d.id=se.driver_id
               WHERE se.session_id=?
                 AND l.is_valid=1
               ORDER BY l.lap_time_ms ASC
               LIMIT 1""",
            (session_id,),
        )

        if not candidates:
            self.log(f"Record skip {track}: nessun giro valido nella sessione {session_id}")
            return

        c = candidates[0]

        rec = self.db.one(
            """SELECT *
               FROM record_windows
               WHERE source_id=?
                 AND track_name=?
                 AND COALESCE(track_layout,'')=?
                 AND window_started_at=?""",
            (source_id, track, layout, window),
        )

        old_lap = int(rec["best_lap_ms"]) if rec and rec["best_lap_ms"] else None

        if old_lap is not None and int(c["lap_time_ms"]) >= old_lap:
            self.log(
                f"Record skip {track}: {c['lap_time_ms']} ms non migliora "
                f"il record attuale {old_lap} ms"
            )
            return

        key = (source_id, track, layout, window)

        current = self.pending_record_candidates.get(key)

        if current and int(c["lap_time_ms"]) >= int(current["lap_ms"]):
            return

        self.pending_record_candidates[key] = {
            "source_id": source_id,
            "src": dict(src),
            "track": track,
            "layout": layout,
            "window": window,
            "lap_ms": int(c["lap_time_ms"]),
            "old_lap": old_lap,
            "driver_id": c["driver_id"],
            "driver_name": c["display_name"],
            "car_name": c["car_name"],
            "session_id": session_id,
            "lap_id": c["lap_id"],
            "session_type": parsed.get("session_type") or "Session",
            "session_datetime": parsed.get("session_datetime") or "",
        }

        self.log(
            f"Record candidato {track}: {c['display_name']} {c['lap_time_ms']} ms"
        )

    def flush_record_announcements(self) -> None:
        if not self.pending_record_candidates:
            return

        now = datetime.now().isoformat(timespec="seconds")

        for key, r in list(self.pending_record_candidates.items()):
            source_id = r["source_id"]
            track = r["track"]
            layout = r["layout"]
            window = r["window"]

            rec = self.db.one(
                """SELECT *
                   FROM record_windows
                   WHERE source_id=?
                     AND track_name=?
                     AND COALESCE(track_layout,'')=?
                     AND window_started_at=?""",
                (source_id, track, layout, window),
            )

            old_lap = int(rec["best_lap_ms"]) if rec and rec["best_lap_ms"] else None

            if old_lap is not None and int(r["lap_ms"]) >= old_lap:
                continue

            if rec:
                self.db.execute(
                    """UPDATE record_windows
                       SET best_lap_ms=?,
                           driver_id=?,
                           driver_name=?,
                           car_name=?,
                           session_id=?,
                           lap_id=?,
                           updated_at=?
                       WHERE id=?""",
                    (
                        r["lap_ms"],
                        r["driver_id"],
                        r["driver_name"],
                        r["car_name"],
                        r["session_id"],
                        r["lap_id"],
                        now,
                        rec["id"],
                    ),
                )
            else:
                self.db.execute(
                    """INSERT INTO record_windows(
                        source_id,
                        track_name,
                        track_layout,
                        window_started_at,
                        best_lap_ms,
                        driver_id,
                        driver_name,
                        car_name,
                        session_id,
                        lap_id,
                        updated_at
                    )
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        source_id,
                        track,
                        layout,
                        window,
                        r["lap_ms"],
                        r["driver_id"],
                        r["driver_name"],
                        r["car_name"],
                        r["session_id"],
                        r["lap_id"],
                        now,
                    ),
                )

            ok, msg = post_discord_record(
                r["src"]["discord_webhook_url"] or "",
                r["src"]["announce_name"] or r["src"]["name"],
                track,
                layout,
                r["driver_name"],
                r["car_name"],
                int(r["lap_ms"]),
                r["session_type"],
                r["session_datetime"],
                old_lap,
            )

            self.db.execute(
                """INSERT INTO record_events(
                    source_id,
                    track_name,
                    track_layout,
                    window_started_at,
                    lap_ms,
                    old_lap_ms,
                    driver_id,
                    driver_name,
                    car_name,
                    session_id,
                    lap_id,
                    session_type,
                    session_datetime,
                    announced_at,
                    discord_status
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    source_id,
                    track,
                    layout,
                    window,
                    int(r["lap_ms"]),
                    old_lap,
                    r["driver_id"],
                    r["driver_name"],
                    r["car_name"],
                    r["session_id"],
                    r["lap_id"],
                    r["session_type"],
                    r["session_datetime"],
                    now,
                    msg,
                ),
            )

            self.log(
                f"Record annunciato {track}: {r['driver_name']} {r['lap_ms']} ms - Discord: {msg}"
            )

        self.pending_record_candidates.clear()

    def check_weekly_recaps(self) -> None:
        now_dt = datetime.now()
        now = now_dt.isoformat(timespec="seconds")

        sources = self.db.query(
            """SELECT *
               FROM import_sources
               WHERE announce_records=1
                 AND weekly_recap_enabled=1
                 AND COALESCE(discord_webhook_url,'')<>''"""
        )

        for src in sources:
            source_id = int(src["id"])

            last = self.db.one(
                """SELECT *
                   FROM record_weekly_recaps
                   WHERE source_id=?
                   ORDER BY sent_at DESC
                   LIMIT 1""",
                (source_id,),
            )

            if last:
                period_start = last["period_end"]
                last_dt = datetime.fromisoformat(last["period_end"])
            else:
                start_raw = src["weekly_recap_started_at"] or src["record_window_started_at"] or now
                last_dt = datetime.fromisoformat(start_raw)
                period_start = start_raw

            if now_dt < last_dt + timedelta(days=7):
                continue

            period_end = now

            rows = self.db.query(
                """SELECT *
                   FROM record_events
                   WHERE source_id=?
                     AND announced_at>=?
                     AND announced_at<?
                   ORDER BY track_name ASC, lap_ms ASC""",
                (source_id, period_start, period_end),
            )

            records = [dict(r) for r in rows]

            ok, msg = post_discord_weekly_recap(
                src["discord_webhook_url"] or "",
                src["announce_name"] or src["name"],
                period_start,
                period_end,
                records,
            )

            self.db.execute(
                """INSERT INTO record_weekly_recaps(
                    source_id,
                    period_start,
                    period_end,
                    sent_at,
                    records_count,
                    discord_status
                )
                VALUES(?,?,?,?,?,?)""",
                (
                    source_id,
                    period_start,
                    period_end,
                    now,
                    len(records),
                    msg,
                ),
            )

            self.log(f"Recap settimanale record {src['name']}: {len(records)} record - Discord: {msg}")

    def _upsert_driver(self, entry: Dict, seen_at: str) -> int:
        steam_id = entry.get("steam_id")
        display_name = entry.get("display_name") or "Unknown driver"
        normalized = normalize_text(display_name)
        nation = entry.get("nation") or ""
        guid = entry.get("driver_key") or ""
        driver_category = entry.get("driver_category") or ""

        if steam_id:
            row = self.db.one("SELECT id FROM drivers WHERE steam_id=?", (steam_id,))
            if row:
                self.db.execute(
                    "UPDATE drivers SET display_name=?, normalized_name=?, nation=?, driver_category=?, guid_key=?, last_seen_at=? WHERE id=?",
                    (display_name, normalized, nation, driver_category, guid, seen_at, row["id"]),
                )
                return int(row["id"])

            cur = self.db.execute(
                "INSERT INTO drivers(steam_id,guid_key,display_name,normalized_name,nation,driver_category,first_seen_at,last_seen_at) VALUES(?,?,?,?,?,?,?,?)",
                (steam_id, guid, display_name, normalized, nation, driver_category, seen_at, seen_at),
            )
            return int(cur.lastrowid)

        row = self.db.one(
            "SELECT id FROM drivers WHERE steam_id IS NULL AND normalized_name=?",
            (normalized,),
        )

        if row:
            self.db.execute(
                "UPDATE drivers SET display_name=?, nation=?, driver_category=?, guid_key=?, last_seen_at=? WHERE id=?",
                (display_name, nation, driver_category, guid, seen_at, row["id"]),
            )
            return int(row["id"])

        cur = self.db.execute(
            "INSERT INTO drivers(steam_id,guid_key,display_name,normalized_name,nation,driver_category,first_seen_at,last_seen_at) VALUES(NULL,?,?,?,?,?,?,?)",
            (guid, display_name, normalized, nation, driver_category, seen_at, seen_at),
        )
        return int(cur.lastrowid)
