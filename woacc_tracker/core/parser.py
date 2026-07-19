import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .utils import key_to_str, make_server_key, parse_datetime_from_filename, display_driver_name

# Nei JSON EVO usati per lo sviluppo, flags==2 indica giro valido.
# flags==129 indica rientro/teletrasporto ai box: il giro successivo e' outlap.
# Gli altri flags vengono conservati per visualizzazione/debug nella lista giri.
VALID_LAP_FLAGS = {2}
PIT_RETURN_FLAGS = {129}


def _invalid_lap_reason(flags: int, outlap_after_pit: bool) -> str:
    if outlap_after_pit:
        return "outlap_after_pit"
    if flags in PIT_RETURN_FLAGS:
        return "pit_return"
    if flags == 1:
        return "invalid_or_outlap"
    if flags not in VALID_LAP_FLAGS:
        return "unknown_flags"
    return ""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _avg(values: List[int]) -> int | None:
    return int(round(sum(values) / len(values))) if values else None


def _normalize_driver_category(value: Any, key: str = "") -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return ""
    if isinstance(value, (int, float)):
        if "cup" in key.lower():
            # ACC cupCategory: 0 Overall/PRO, 1 PRO-AM, 2 AM, 3 SILVER.
            mapping = {0: "PRO", 1: "PRO-AM", 2: "AM", 3: "SILVER", 4: "NATIONAL"}
        else:
            # Mappatura prudente: se il gioco usa enum diversi, il valore resta comunque leggibile.
            mapping = {0: "AM", 1: "SILVER", 2: "PRO", 3: "PRO-AM", 4: "PLATINUM"}
        return mapping.get(int(value), str(int(value))).upper()
    text = str(value).strip()
    if not text:
        return ""
    normalized = text.replace("_", " ").replace("-", " ").upper()
    if "PRO AM" in normalized:
        return "PRO-AM"
    if "SILVER" in normalized:
        return "SILVER"
    if normalized in {"AM", "BRONZE", "GENTLEMAN"} or " AM" in f" {normalized} ":
        return "AM"
    if "PRO" in normalized or "PLATINUM" in normalized:
        return "PRO"
    return text.upper()


def _find_driver_category(*objects: Any) -> str:
    wanted = (
        "category", "driver_category", "drivercategory", "driver_category_name",
        "cup_category", "cupcategory", "class", "driver_class", "rating", "licence", "license"
    )

    def walk(obj: Any) -> str:
        if isinstance(obj, dict):
            for key, value in obj.items():
                k = str(key).lower()
                if any(w in k for w in wanted):
                    found = _normalize_driver_category(value, str(key))
                    if found:
                        return found
            for value in obj.values():
                found = walk(value)
                if found:
                    return found
        elif isinstance(obj, list):
            for value in obj:
                found = walk(value)
                if found:
                    return found
        return ""

    for obj in objects:
        found = walk(obj)
        if found:
            return found
    return ""


def parse_evo_results(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    server_name = data.get("server_name") or "Unknown server"
    track_name = data.get("track_name") or "Unknown track"
    track_layout = data.get("track_layout_name") or ""
    session_type = data.get("session_type") or "Unknown"
    session_dt = parse_datetime_from_filename(str(path))

    drivers_by_key = {key_to_str(d.get("guid")): d for d in data.get("drivers", [])}
    cars_by_key = {key_to_str(c.get("car_id")): c for c in data.get("cars", [])}

    grouped_laps: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for lap in data.get("laps", []) or []:
        dkey = key_to_str(lap.get("driver_key"))
        ckey = key_to_str(lap.get("car_key"))
        if dkey and ckey and int(lap.get("time") or 0) > 0:
            grouped_laps[(dkey, ckey)].append(lap)

    entries: List[Dict[str, Any]] = []
    standings_order = [key_to_str(k) for k in data.get("driver_standings", []) or []]
    standing_index = {k: i + 1 for i, k in enumerate(standings_order)}
    time_standings = data.get("time_standings", []) or []
    standing_time_by_driver = {
        key: (time_standings[i] if i < len(time_standings) else None)
        for i, key in enumerate(standings_order)
    }

    for (driver_key, car_key), laps in grouped_laps.items():
        driver = drivers_by_key.get(driver_key, {})
        car = cars_by_key.get(car_key, {})
        parsed_laps = []
        valid_times: List[int] = []
        all_times: List[int] = []
        valid_s1: List[int] = []
        valid_s2: List[int] = []
        valid_s3: List[int] = []

        next_lap_is_outlap = False

        for idx, lap in enumerate(laps, start=1):
            flags = int(lap.get("flags") or 0)
            is_valid = flags in VALID_LAP_FLAGS and not next_lap_is_outlap
            invalid_reason = "" if is_valid else _invalid_lap_reason(flags, next_lap_is_outlap)
            lap_time = int(lap.get("time") or 0)
            split = lap.get("split") or []
            s1 = int(split[0]) if len(split) > 0 and split[0] is not None else None
            s2 = int(split[1]) if len(split) > 1 and split[1] is not None else None
            s3 = int(split[2]) if len(split) > 2 and split[2] is not None else None

            if lap_time > 0:
                all_times.append(lap_time)
            if is_valid and lap_time > 0:
                valid_times.append(lap_time)
                if s1: valid_s1.append(s1)
                if s2: valid_s2.append(s2)
                if s3: valid_s3.append(s3)

            parsed_laps.append({
                "lap_number": idx,
                "lap_time_ms": lap_time,
                "is_valid": is_valid,
                "invalid_reason": invalid_reason,
                "flags": flags,
                "s1_ms": s1,
                "s2_ms": s2,
                "s3_ms": s3,
            })

            next_lap_is_outlap = flags in PIT_RETURN_FLAGS

        best_lap = min(valid_times) if valid_times else None
        potential_lap = (min(valid_s1) + min(valid_s2) + min(valid_s3)) if valid_s1 and valid_s2 and valid_s3 else None

        entries.append({
            "driver_key": driver_key,
            "steam_id": str(driver.get("player_id") or "").strip() or None,
            "display_name": display_driver_name(driver),
            "nation": driver.get("nation") or "",
            "driver_category": _find_driver_category(driver, car),
            "car_key": car_key,
            "car_name": car.get("model_displayname") or "Unknown car",
            "race_number": car.get("race_number"),
            "position": standing_index.get(driver_key),
            "standing_time_ms": standing_time_by_driver.get(driver_key),
            "best_lap_ms": best_lap,
            "potential_lap_ms": potential_lap,
            "avg_valid_lap_ms": _avg(valid_times),
            "avg_all_lap_ms": _avg(all_times),
            "laps_total": len(parsed_laps),
            "laps_valid": len(valid_times),
            "laps": parsed_laps,
        })

    if session_type.lower() in {"practice", "qualify", "warmup"}:
        entries.sort(key=lambda e: (e["best_lap_ms"] is None, e["best_lap_ms"] or 10**12, e["display_name"]))
        for i, e in enumerate(entries, start=1):
            e["position"] = i
            if entries and entries[0].get("best_lap_ms") and e.get("best_lap_ms"):
                e["gap_ms"] = e["best_lap_ms"] - entries[0]["best_lap_ms"]
            else:
                e["gap_ms"] = None
    elif session_type.lower() == "race":
        entries.sort(key=lambda e: (e.get("position") is None, e.get("position") or 10**9, e["display_name"]))
        leader_time = entries[0].get("standing_time_ms") if entries else None
        for e in entries:
            e["race_total_time_ms"] = e.get("standing_time_ms") if e.get("standing_time_ms") else None
            if leader_time and e.get("standing_time_ms"):
                e["gap_ms"] = int(e["standing_time_ms"]) - int(leader_time)
            else:
                e["gap_ms"] = None
            e["status"] = "Finished" if e.get("laps_total", 0) > 0 else "No laps"
    else:
        entries.sort(key=lambda e: (e["best_lap_ms"] is None, e["best_lap_ms"] or 10**12, e["display_name"]))
        for i, e in enumerate(entries, start=1):
            e["position"] = i

    total_laps = sum(e["laps_total"] for e in entries)
    best_session_lap = min([e["best_lap_ms"] for e in entries if e.get("best_lap_ms")] or [None])

    return {
        "file_hash": file_sha256(path),
        "file_path": str(path),
        "server_name": server_name,
        "track_name": track_name,
        "track_layout": track_layout,
        "server_key": make_server_key(server_name, track_name, track_layout),
        "session_name": data.get("session_name") or "",
        "session_type": session_type,
        "session_datetime": session_dt,
        "is_completed": bool(data.get("is_completed")),
        "laps_total": total_laps,
        "drivers_count": len(entries),
        "best_lap_ms": best_session_lap,
        "entries": entries,
    }
