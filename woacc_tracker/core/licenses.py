from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .database import Database
from .discord_notifications import post_license_notification
from .translations import DEFAULT_LANGUAGE


def parse_license_levels(value: str | None) -> List[Dict[str, Any]]:
    try:
        raw = json.loads(value or "[]")
    except Exception:
        raw = []
    levels = []
    for item in raw:
        name = str(item.get("name") or "").strip()
        try:
            time_ms = int(item.get("time_ms") or 0)
        except Exception:
            time_ms = 0
        if name and time_ms > 0:
            levels.append({"name": name, "time_ms": time_ms})
    # slowest threshold first, fastest/hardest last; rank increases with difficulty
    levels.sort(key=lambda x: x["time_ms"], reverse=True)
    return levels[:3]


def best_license_for_time(lap_ms: int, levels: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    best = None
    for idx, lvl in enumerate(levels, start=1):
        if lap_ms <= int(lvl["time_ms"]):
            best = {"name": lvl["name"], "time_ms": int(lvl["time_ms"]), "rank": idx}
    return best


def process_license_notifications(db: Database, source_id: int, session_id: int, src: Dict[str, Any], lang: str = DEFAULT_LANGUAGE, log=print) -> None:
    if not src or not int(src.get("license_enabled") or 0):
        return
    webhook = (src.get("license_webhook_url") or "").strip()
    levels = parse_license_levels(src.get("license_levels_json"))
    if not levels:
        return

    rows = db.query(
        """SELECT se.id AS entry_id,
                  se.best_lap_ms,
                  d.id AS driver_id,
                  d.steam_id,
                  d.display_name
           FROM session_entries se
           JOIN drivers d ON d.id=se.driver_id
           WHERE se.session_id=?
             AND se.best_lap_ms IS NOT NULL
             AND se.best_lap_ms > 0
           ORDER BY se.best_lap_ms ASC""",
        (session_id,),
    )
    now = datetime.now().isoformat(timespec="seconds")

    for r in rows:
        steam_id = (r["steam_id"] or "").strip()
        if not steam_id:
            # SteamID resta interno, ma è necessario come chiave stabile.
            continue
        lap_ms = int(r["best_lap_ms"])
        lic = best_license_for_time(lap_ms, levels)
        if not lic:
            continue

        old = db.one("SELECT * FROM license_achievements WHERE source_id=? AND steam_id=?", (source_id, steam_id))
        old_rank = int(old["license_rank"]) if old else 0
        old_best = int(old["best_time_ms"]) if old and old["best_time_ms"] else None
        should_notify = int(lic["rank"]) > old_rank
        status = "not announced"

        if should_notify and webhook:
            ok, status = post_license_notification(webhook, r["display_name"], lic["name"], lap_ms, session_id, lang)
        elif should_notify:
            status = "missing webhook"

        if old:
            # Se migliora il tempo ma resta nella stessa licenza, aggiorna classifica senza rinotificare.
            if int(lic["rank"]) > old_rank or old_best is None or lap_ms < old_best:
                db.execute(
                    """UPDATE license_achievements
                       SET driver_id=?, driver_name=?, license_name=?, license_rank=?, best_time_ms=?, session_id=?, updated_at=?, discord_status=?
                       WHERE id=?""",
                    (r["driver_id"], r["display_name"], lic["name"], int(lic["rank"]), lap_ms, session_id, now, status if should_notify else old["discord_status"], old["id"]),
                )
        else:
            db.execute(
                """INSERT INTO license_achievements(
                    source_id, steam_id, driver_id, driver_name, license_name, license_rank,
                    best_time_ms, session_id, achieved_at, updated_at, discord_status
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (source_id, steam_id, r["driver_id"], r["display_name"], lic["name"], int(lic["rank"]), lap_ms, session_id, now, now, status),
            )

        if should_notify:
            log(f"Licenza {lic['name']} per {r['display_name']} ({lap_ms} ms): {status}")
