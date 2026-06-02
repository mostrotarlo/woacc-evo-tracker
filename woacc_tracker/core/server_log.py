import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


LOG_PREFIX_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s+\[[^\]]+\]\s+\[[^\]]+\]\s?(?P<msg>.*)$")
MAX_WEATHER_MATCH_SECONDS = 12 * 60 * 60


def _line_parts(line: str) -> tuple[Optional[str], str]:
    match = LOG_PREFIX_RE.match(line)
    if not match:
        return None, line.rstrip("\n")
    return match.group("ts"), match.group("msg").rstrip("\n")


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

    return {
        "weather_log_at": ts.isoformat(timespec="seconds") if ts else "",
        "server_name": definition.get("name") or "",
        "session_type": definition.get("gamemode_type") or session.get("name") or "",
        "track_name": track.get("name") or "",
        "track_layout": scene.get("track_layout_name") or "",
        "ambient_temperature_c": static_weather.get("ambient_temperature_c"),
        "weather_type": _clean_enum(weather.get("weather_type") or session.get("weather_type")),
        "sky_coverage": static_weather.get("sky_coverage"),
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

    for ts, definition in _iter_season_definitions(path):
        item = _weather_from_definition(ts, definition)
        if server_name and item.get("server_name") and not _same_text(server_name, item["server_name"]):
            continue
        if track_name and item.get("track_name") and not _same_text(track_name, item["track_name"]):
            continue
        if track_layout and item.get("track_layout") and not _same_text(track_layout, item["track_layout"]):
            continue

        if target_dt and ts:
            if ts > target_dt:
                continue
            delta = abs((target_dt - ts).total_seconds())
            if delta > MAX_WEATHER_MATCH_SECONDS:
                continue
            if best_delta is not None and delta >= best_delta:
                continue
            best_delta = delta

        best = item

    return best
