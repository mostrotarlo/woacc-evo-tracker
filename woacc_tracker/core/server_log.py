import json
import copy
import re
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any, Dict, Iterable, Optional


LOG_PREFIX_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s+\[[^\]]+\]\s+\[[^\]]+\]\s?(?P<msg>.*)$")
PLAYERS_RE = re.compile(r"Server updated:\s*(?P<count>\d+)\s+players", re.IGNORECASE)
CAR_DRIVER_RE = re.compile(r"Car \[(?P<car_id>[^\]]+)\].*? for driver (?P<driver>.*?) \[")
CONNECT_RE = re.compile(r"(?P<steam_id>\d+)\s+connected \(true\) on car (?P<car>[^,]+), with new carId (?P<car_id>\S+)", re.IGNORECASE)
DISCONNECT_RE = re.compile(
    r"(?:(?P<steam_id>\d+)\s+connected \(false\).*?(?:carId (?P<car_id>\S+))?"
    r"|Disconnected carId (?P<car_id2>\S+)"
    r"|Removing disconnected remote_car (?P<car_id3>\S+)"
    r"|Car \[(?P<car_id4>[^\]]+)\].*disconnect)",
    re.IGNORECASE
)
NEW_LAP_RE = re.compile(r"New lap carId (?P<car_id>[^:]+):\s*(?P<min>\d\d):(?P<sec>\d\d\.\d+)")
SPLIT_RE = re.compile(r"On Split start .*? id (?P<split_id>\d+) splittime (?P<time>\d+)")
INVALID_PIT_RE = re.compile(r"invalid pit id (?P<car_id>\S+)", re.IGNORECASE)
TELEPORT_RE = re.compile(r"Teleporting (?P<car_id>\S+)", re.IGNORECASE)
SESSION_START_RE = re.compile(r"(?:TimeAttackRemote|RaceRemote|QualifyingRemote)\s+.+\s+created", re.IGNORECASE)
SESSION_RESET_RE = re.compile(r"END_SESSION|OnExitGamemode|chaging GameMode", re.IGNORECASE)
MAX_WEATHER_MATCH_SECONDS = 12 * 60 * 60
LIVE_TAIL_BYTES = 512 * 1024
LIVE_STATUS_TAIL_BYTES = 64 * 1024
LIVE_HEAD_BYTES = 512 * 1024
LIVE_ONLINE_SECONDS = 180
LIVE_CACHE_SECONDS = 5
_LIVE_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}


def _line_parts(line: str) -> tuple[Optional[str], str]:
    match = LOG_PREFIX_RE.match(line)
    if not match:
        return None, line.rstrip("\n")
    return match.group("ts"), match.group("msg").rstrip("\n")


def _source_cache_key(prefix: str, source: Dict[str, Any], detail: str = "") -> str:
    return "|".join([
        prefix,
        detail,
        str(source.get("name") or ""),
        str(source.get("path") or ""),
        str(source.get("server_log_path") or ""),
    ])


def _cfg_cache_key(prefix: str, cfg: Dict[str, Any], detail: str = "") -> str:
    parts = [prefix, detail]
    for source in cfg.get("sources") or []:
        parts.extend([
            str(source.get("enabled", True)),
            str(source.get("live_leaderboard_enabled", "")),
            str(source.get("name") or ""),
            str(source.get("path") or ""),
            str(source.get("server_log_path") or ""),
        ])
    return "|".join(parts)


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    item = _LIVE_CACHE.get(key)
    if not item:
        return None
    ts, value = item
    if monotonic() - ts > LIVE_CACHE_SECONDS:
        _LIVE_CACHE.pop(key, None)
        return None
    return copy.deepcopy(value)


def _cache_set(key: str, value: Dict[str, Any]) -> Dict[str, Any]:
    _LIVE_CACHE[key] = (monotonic(), copy.deepcopy(value))
    return value


def _parse_ts(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _same_text(left: str, right: str) -> bool:
    return (left or "").strip().lower() == (right or "").strip().lower()


def _clean_enum(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "_" in text:
        text = text.rsplit("_", 1)[-1]
    return text.replace("_", " ").strip().upper()


def _first_session(definition: Dict[str, Any]) -> Dict[str, Any]:
    event_map = definition.get("event_map") or {}
    for event in event_map.values():
        session_map = event.get("session_map") or {}
        for session in session_map.values():
            if isinstance(session, dict):
                return session
    return {}


def _weather_from_definition(ts: Optional[datetime], definition: Dict[str, Any]) -> Dict[str, Any]:
    session = _first_session(definition)
    scene = session.get("scene") or {}
    track = scene.get("track_content_data") or {}
    weather = session.get("weather") or {}
    static_weather = (((weather.get("static_data") or {}).get("static_weather") or {}))
    dynamic_track = weather.get("dynamic_track_condition") or session.get("dynamic_track_condition") or {}

    ambient_temperature = static_weather.get("ambient_temperature_c")
    mean_ambient_temperature = static_weather.get("mean_ambient_temperature_c")
    if ambient_temperature in (None, 0, 0.0) and mean_ambient_temperature is not None:
        ambient_temperature = mean_ambient_temperature

    sky_coverage = static_weather.get("sky_coverage")
    if sky_coverage is None:
        sky_coverage = static_weather.get("cloud_coverage")

    return {
        "weather_log_at": ts.isoformat(timespec="seconds") if ts else "",
        "server_name": definition.get("name") or "",
        "session_type": _clean_enum(definition.get("gamemode_type") or session.get("name")),
        "track_name": track.get("name") or "",
        "track_layout": scene.get("track_layout_name") or "",
        "ambient_temperature_c": ambient_temperature,
        "weather_type": _clean_enum(weather.get("weather_type") or session.get("weather_type")),
        "sky_coverage": sky_coverage,
        "gloominess": static_weather.get("gloominess"),
        "precipitation": static_weather.get("precipitation"),
        "fog": static_weather.get("fog"),
        "humidity": static_weather.get("humidity"),
        "pressure_psi": static_weather.get("pressure_psi"),
        "wind_speed_m_s": static_weather.get("wind_speed_m_s"),
        "wind_gust": static_weather.get("wind_gust"),
        "wind_direction_deg": static_weather.get("wind_direction_deg"),
        "initial_global_wetness": static_weather.get("initial_global_wetness"),
        "is_dynamic_weather": static_weather.get("is_dynamic_weather"),
        "initial_grip_label": _clean_enum(weather.get("initial_grip") or session.get("initial_grip")),
        "track_grip": dynamic_track.get("initial_grip"),
        "track_rubber": dynamic_track.get("rubber"),
        "track_marbles": dynamic_track.get("marbles"),
    }


def _iter_season_definitions(path: Path):
    current_ts: Optional[datetime] = None
    collecting = False
    lines: list[str] = []
    balance = 0

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            ts_raw, msg = _line_parts(raw)
            if msg == "Season Definition":
                current_ts = _parse_ts(ts_raw)
                collecting = False
                lines = []
                balance = 0
                continue

            if current_ts and msg.lstrip().startswith("{") and not collecting:
                collecting = True

            if not collecting:
                continue

            lines.append(msg)
            balance += msg.count("{") - msg.count("}")

            if balance == 0 and lines:
                try:
                    yield current_ts, json.loads("\n".join(lines))
                except Exception:
                    pass
                current_ts = None
                collecting = False
                lines = []


def _tail_lines(path: Path, max_bytes: int = LIVE_TAIL_BYTES) -> list[str]:
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            if size > max_bytes:
                f.seek(-max_bytes, 2)
                f.readline()
            raw = f.read()
        return raw.decode("utf-8", errors="ignore").splitlines()
    except Exception:
        return []


def _head_lines(path: Path, max_bytes: int = LIVE_HEAD_BYTES) -> list[str]:
    try:
        with path.open("rb") as f:
            raw = f.read(max_bytes)
        return raw.decode("utf-8", errors="ignore").splitlines()
    except Exception:
        return []


def _iter_season_definitions_from_lines(lines: Iterable[str]):
    current_ts: Optional[datetime] = None
    collecting = False
    collected: list[str] = []
    balance = 0

    for raw in lines:
        ts_raw, msg = _line_parts(raw)
        if msg == "Season Definition":
            current_ts = _parse_ts(ts_raw)
            collecting = False
            collected = []
            balance = 0
            continue

        if current_ts and msg.lstrip().startswith("{") and not collecting:
            collecting = True

        if not collecting:
            continue

        collected.append(msg)
        balance += msg.count("{") - msg.count("}")

        if balance == 0 and collected:
            try:
                yield current_ts, json.loads("\n".join(collected))
            except Exception:
                pass
            current_ts = None
            collecting = False
            collected = []


def _weather_candidates_from_log(path: Path) -> list[Dict[str, Any]]:
    try:
        stat = path.stat()
    except Exception:
        return []

    cache_key = f"weather_candidates|{path}|{stat.st_size}|{stat.st_mtime_ns}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return list(cached.get("items") or [])

    lines = _head_lines(path) + _tail_lines(path)
    items: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for ts, definition in _iter_season_definitions_from_lines(lines):
        key = f"{ts.isoformat() if ts else ''}|{definition.get('name') or ''}"
        if key in seen:
            continue
        seen.add(key)
        items.append(_weather_from_definition(ts, definition))

    _cache_set(cache_key, {"items": items})
    return items


def read_live_server_status(source: Dict[str, Any], now: Optional[datetime] = None, include_details: bool = True) -> Dict[str, Any]:
    cache_key = _source_cache_key("status", source, "details" if include_details else "light")
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    log_path = (source.get("server_log_path") or "").strip()
    path = Path(log_path) if log_path else None
    status: Dict[str, Any] = {
        "source_name": source.get("name") or "",
        "server_name": source.get("name") or "",
        "log_path": log_path,
        "has_log": bool(path and path.exists() and path.is_file()),
        "is_online": False,
        "last_log_at": "",
        "players_online": 0,
    }
    if not path or not path.exists() or not path.is_file():
        return _cache_set(cache_key, status)

    lines = _tail_lines(path, LIVE_TAIL_BYTES if include_details else LIVE_STATUS_TAIL_BYTES)
    if not lines:
        return _cache_set(cache_key, status)

    last_ts: Optional[datetime] = None
    latest_players: Optional[int] = None
    for line in lines:
        ts_raw, msg = _line_parts(line)
        parsed_ts = _parse_ts(ts_raw)
        if parsed_ts:
            last_ts = parsed_ts
        players_match = PLAYERS_RE.search(msg)
        if players_match:
            try:
                latest_players = int(players_match.group("count"))
            except ValueError:
                pass

    if include_details:
        latest_definition: Optional[Dict[str, Any]] = None
        latest_definition_ts: Optional[datetime] = None
        for ts, definition in _iter_season_definitions_from_lines(lines):
            latest_definition = definition
            latest_definition_ts = ts
        if latest_definition is None:
            for ts, definition in _iter_season_definitions_from_lines(_head_lines(path)):
                latest_definition = definition
                latest_definition_ts = ts

        if latest_definition:
            weather = _weather_from_definition(latest_definition_ts, latest_definition)
            status.update(weather)
            status["server_name"] = weather.get("server_name") or status["server_name"]
            status["session_type"] = weather.get("session_type") or ""

    if latest_players is not None:
        status["players_online"] = latest_players
    if last_ts:
        status["last_log_at"] = last_ts.isoformat(timespec="seconds")
        ref = now or datetime.now()
        status["is_online"] = abs((ref - last_ts).total_seconds()) <= LIVE_ONLINE_SECONDS

    return _cache_set(cache_key, status)


def is_live_leaderboard_enabled(source: Dict[str, Any]) -> bool:
    return bool(source.get("live_leaderboard_enabled", False))


def read_live_servers_status(cfg: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
    cache_key = _cfg_cache_key("servers_status", cfg, "details" if include_details else "light")
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    items = []
    for index, source in enumerate(cfg.get("sources") or []):
        if not source.get("enabled", True):
            continue
        if not is_live_leaderboard_enabled(source):
            continue
        item = read_live_server_status(source, include_details=include_details)
        item["source_index"] = index
        if item.get("has_log"):
            items.append(item)
    online = [item for item in items if item.get("is_online")]
    return _cache_set(cache_key, {
        "items": items,
        "online": online,
        "has_logs": bool(items),
        "active_count": len(online),
        "players_online": sum(int(item.get("players_online") or 0) for item in online),
    })


def _lap_ms(min_text: str, sec_text: str) -> int:
    return int((int(min_text) * 60 + float(sec_text)) * 1000)


def _clean_live_car_name(value: str) -> str:
    text = (value or "").strip()
    if text.lower().startswith("ks_"):
        text = text[3:]
    return text.replace("_", " ").strip()


def _compact_car_id(value: str) -> str:
    return (value or "").replace("-", "").strip().lower()


def _find_lap_splits(split_events: list[tuple[int, int]], lap_time_ms: int) -> tuple[Optional[int], Optional[int], Optional[int]]:
    for end_idx in range(len(split_events) - 1, -1, -1):
        if split_events[end_idx][0] != 2:
            continue
        s3 = split_events[end_idx][1]
        for mid_idx in range(end_idx - 1, -1, -1):
            if split_events[mid_idx][0] != 1:
                continue
            s2 = split_events[mid_idx][1]
            for start_idx in range(mid_idx - 1, -1, -1):
                if split_events[start_idx][0] != 0:
                    continue
                s1 = split_events[start_idx][1]
                if abs((s1 + s2 + s3) - lap_time_ms) <= 2:
                    return s1, s2, s3
    return None, None, None


def _current_online_car_ids(lines: Iterable[str]) -> tuple[set[str], bool]:
    online: set[str] = set()
    compact_to_car: Dict[str, str] = {}
    steam_to_car: Dict[str, str] = {}
    has_driver_state = False
    for line in lines:
        _, msg = _line_parts(line)
        connect_match = CONNECT_RE.search(msg)
        if connect_match:
            car_id = connect_match.group("car_id")
            steam_to_car[connect_match.group("steam_id")] = car_id
            online.add(car_id)
            compact_to_car[_compact_car_id(car_id)] = car_id
            has_driver_state = True
            continue

        disconnect_match = DISCONNECT_RE.search(msg)
        if disconnect_match:
            has_driver_state = True
            car_id = (
                disconnect_match.group("car_id")
                or disconnect_match.group("car_id2")
                or disconnect_match.group("car_id3")
                or disconnect_match.group("car_id4")
                or steam_to_car.get(disconnect_match.group("steam_id") or "")
            )
            if car_id:
                car_id = compact_to_car.get(_compact_car_id(car_id), car_id)
                online.discard(car_id)
            continue

        players_match = PLAYERS_RE.search(msg)
        if players_match:
            try:
                if int(players_match.group("count")) == 0:
                    online.clear()
                    steam_to_car.clear()
                    has_driver_state = True
            except ValueError:
                pass
    return online, has_driver_state


def _car_activity_ids(lines: Iterable[str]) -> set[str]:
    active: set[str] = set()
    for line in lines:
        _, msg = _line_parts(line)
        for pattern, groups in (
            (CONNECT_RE, ("car_id",)),
            (NEW_LAP_RE, ("car_id",)),
            (INVALID_PIT_RE, ("car_id",)),
            (TELEPORT_RE, ("car_id",)),
        ):
            match = pattern.search(msg)
            if not match:
                continue
            for group in groups:
                car_id = match.group(group)
                if car_id:
                    active.add(car_id)
            break
    return active


def _active_session_start_index(lines: list[str]) -> int:
    active_start_index = 0
    for index, line in enumerate(lines):
        _, msg = _line_parts(line)
        if msg == "Season Definition" or SESSION_RESET_RE.search(msg):
            active_start_index = index + 1
            continue
        if SESSION_START_RE.search(msg):
            active_start_index = index + 1
            continue
        players_match = PLAYERS_RE.search(msg)
        if players_match:
            try:
                if int(players_match.group("count")) == 0:
                    active_start_index = index + 1
            except ValueError:
                pass
    return active_start_index


def read_live_server_leaderboard(source: Dict[str, Any]) -> Dict[str, Any]:
    cache_key = _source_cache_key("leaderboard", source)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    status = read_live_server_status(source)
    result: Dict[str, Any] = {
        "status": status,
        "entries": [],
        "race_pending": False,
        "is_provisional": True,
    }
    log_path = (source.get("server_log_path") or "").strip()
    path = Path(log_path) if log_path else None
    if not path or not path.exists() or not path.is_file():
        return _cache_set(cache_key, result)

    session_type = str(status.get("session_type") or "").strip().upper()
    if session_type in {"RACE", "R"}:
        result["race_pending"] = True
        return _cache_set(cache_key, result)
    if int(status.get("players_online") or 0) <= 0:
        return _cache_set(cache_key, result)

    raw_lines = _tail_lines(path, max_bytes=max(LIVE_TAIL_BYTES * 4, 2 * 1024 * 1024))
    car_names: Dict[str, str] = {}
    car_models: Dict[str, str] = {}
    for line in raw_lines:
        _, msg = _line_parts(line)
        car_match = CAR_DRIVER_RE.search(msg)
        if car_match:
            car_names[car_match.group("car_id")] = car_match.group("driver").strip()
            continue

        connect_match = CONNECT_RE.search(msg)
        if connect_match:
            car_models[connect_match.group("car_id")] = _clean_live_car_name(connect_match.group("car"))
            continue

    active_start_index = _active_session_start_index(raw_lines)
    lines = raw_lines[active_start_index:]
    current_online, online_state_known = _current_online_car_ids(lines)
    players_online_count = int(status.get("players_online") or 0)
    latest_player_count_index = -1
    for index, line in enumerate(lines):
        _, msg = _line_parts(line)
        if PLAYERS_RE.search(msg):
            latest_player_count_index = index

    inferred_online: set[str] = set()
    inferred_online_mode = False
    if players_online_count > 0 and len(current_online) > players_online_count:
        inferred_online = _car_activity_ids(lines[latest_player_count_index + 1:])
        if len(inferred_online) > players_online_count:
            inferred_online.clear()
        inferred_online_mode = bool(inferred_online)
        current_online = inferred_online
        online_state_known = inferred_online_mode
    laps_by_car: Dict[str, list[Dict[str, Any]]] = {}
    split_events: list[tuple[int, int]] = []

    for line in lines:
        _, msg = _line_parts(line)
        car_match = CAR_DRIVER_RE.search(msg)
        if car_match:
            car_names[car_match.group("car_id")] = car_match.group("driver").strip()
            continue

        connect_match = CONNECT_RE.search(msg)
        if connect_match:
            car_models[connect_match.group("car_id")] = _clean_live_car_name(connect_match.group("car"))
            continue

        invalid_match = INVALID_PIT_RE.search(msg)
        if invalid_match:
            continue

        teleport_match = TELEPORT_RE.search(msg)
        if teleport_match:
            continue

        split_match = SPLIT_RE.search(msg)
        if split_match:
            try:
                split_events.append((int(split_match.group("split_id")), int(split_match.group("time"))))
                split_events = split_events[-48:]
            except ValueError:
                pass
            continue

        lap_match = NEW_LAP_RE.search(msg)
        if not lap_match:
            continue

        car_id = lap_match.group("car_id")
        lap_time_ms = _lap_ms(lap_match.group("min"), lap_match.group("sec"))
        s1_ms, s2_ms, s3_ms = _find_lap_splits(split_events, lap_time_ms)
        laps_by_car.setdefault(car_id, []).append({
            "lap_number": len(laps_by_car.get(car_id, [])) + 1,
            "lap_time_ms": lap_time_ms,
            "s1_ms": s1_ms,
            "s2_ms": s2_ms,
            "s3_ms": s3_ms,
            "is_valid": True,
            "validity": "candidate",
            "reason": "",
        })

    entries = []
    for car_id, laps in laps_by_car.items():
        candidate_laps = [lap for lap in laps if lap["validity"] != "invalid_known"]
        best = min((lap["lap_time_ms"] for lap in candidate_laps), default=None)
        is_online = online_state_known and car_id in current_online
        online_state = "online" if is_online else ("unknown" if inferred_online_mode else ("offline" if online_state_known else "unknown"))
        entries.append({
            "car_id": car_id,
            "driver": car_names.get(car_id) or car_id,
            "car": car_models.get(car_id) or "",
            "is_online": is_online,
            "online_state": online_state,
            "laps_total": len(laps),
            "laps_valid": len(candidate_laps),
            "laps_confirmed_valid": 0,
            "laps_candidate": len(candidate_laps),
            "best_lap_ms": best,
            "last_lap_ms": laps[-1]["lap_time_ms"] if laps else None,
            "last_s1_ms": laps[-1].get("s1_ms") if laps else None,
            "last_s2_ms": laps[-1].get("s2_ms") if laps else None,
            "last_s3_ms": laps[-1].get("s3_ms") if laps else None,
            "laps": laps,
        })

    entries.sort(key=lambda item: (item["best_lap_ms"] is None, item["best_lap_ms"] or 10**12, item["driver"].lower()))
    leader_best = next((item["best_lap_ms"] for item in entries if item["best_lap_ms"] is not None), None)
    for pos, item in enumerate(entries, 1):
        item["position"] = pos
        item["gap_ms"] = None if leader_best is None or item["best_lap_ms"] is None else item["best_lap_ms"] - leader_best
    result["entries"] = entries
    result["online_entries"] = sum(1 for item in entries if item.get("is_online"))
    result["offline_entries"] = sum(1 for item in entries if item.get("online_state") == "offline")
    result["unknown_entries"] = sum(1 for item in entries if item.get("online_state") == "unknown")
    return _cache_set(cache_key, result)


def find_session_weather(
    log_path: str,
    session_datetime: str,
    server_name: str,
    track_name: str,
    track_layout: str,
) -> Dict[str, Any]:
    path = Path(log_path)
    if not log_path or not path.exists() or not path.is_file():
        return {}

    try:
        target_dt = datetime.fromisoformat(session_datetime)
    except Exception:
        target_dt = None

    best: Dict[str, Any] = {}
    best_delta: Optional[float] = None
    latest_matching: Dict[str, Any] = {}
    latest_matching_ts: Optional[datetime] = None

    for item in _weather_candidates_from_log(path):
        if server_name and item.get("server_name") and not _same_text(server_name, item["server_name"]):
            continue
        if track_name and item.get("track_name") and not _same_text(track_name, item["track_name"]):
            continue
        if track_layout and item.get("track_layout") and not _same_text(track_layout, item["track_layout"]):
            continue

        item_ts = _parse_ts(item.get("weather_log_at"))
        if item_ts and target_dt and item_ts <= target_dt:
            if latest_matching_ts is None or item_ts > latest_matching_ts:
                latest_matching_ts = item_ts
                latest_matching = item
        elif not target_dt:
            latest_matching = item

        if target_dt and item_ts:
            if item_ts > target_dt:
                continue
            delta = abs((target_dt - item_ts).total_seconds())
            if delta > MAX_WEATHER_MATCH_SECONDS:
                continue
            if best_delta is not None and delta >= best_delta:
                continue
            best_delta = delta

        best = item

    return best or latest_matching
