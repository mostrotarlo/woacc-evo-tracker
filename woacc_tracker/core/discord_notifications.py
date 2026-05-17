from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from .records_discord import _post_discord
from .utils import ms_to_time
from .translations import DEFAULT_LANGUAGE, load_vocabulary
from .config import load_config


def _tr(lang: str, key: str, default: str) -> str:
    try:
        return str(load_vocabulary((lang or DEFAULT_LANGUAGE).lower()).get(key, default))
    except Exception:
        return default


def _tracker_url(session_id: Optional[int] = None) -> str:
    try:
        cfg = load_config()
    except Exception:
        cfg = {}

    public_url = (cfg.get("public_url") or "").strip().rstrip("/")
    base_path = (cfg.get("base_path") or "").strip()

    if not public_url:
        return "WOACC Tracker"

    # normalizza /tracker
    if base_path:
        base_path = "/" + base_path.strip("/")

        # evita doppio /tracker
        if not public_url.endswith(base_path):
            public_url += base_path

    if session_id:
        return f"{public_url}/session/{session_id}"

    return public_url


def post_session_notification(
    webhook_url: str,
    announce_name: str,
    session_id: int,
    session_type: str,
    server_name: str,
    track_name: str,
    session_datetime: str,
    top_rows: Optional[List[Dict[str, Any]]] = None,
    detailed: bool = False,
    lang: str = DEFAULT_LANGUAGE,
) -> tuple[bool, str]:
    session_type = session_type or "Session"
    title = _tr(lang, "discord_session_available_title", "📢 New session available")
    desc = f"**{server_name or announce_name or 'WOACC Tracker'}**\n{track_name or 'Unknown track'} · {session_type}\n{session_datetime or ''}\n\n{_tracker_url(session_id)}"

    fields = [
        {"name": _tr(lang, "discord_event", "Event"), "value": announce_name or "WOACC Tracker", "inline": True},
        {"name": _tr(lang, "discord_track", "Track"), "value": track_name or "—", "inline": True},
        {"name": _tr(lang, "discord_session", "Session"), "value": session_type, "inline": True},
    ]

    if detailed and top_rows and session_type.lower() in {"qualify", "qualifying", "q", "race", "r"}:
        lines = []
        for i, r in enumerate(top_rows[:3], start=1):
            name = r.get("driver_name") or r.get("display_name") or "—"
            lap = r.get("best_lap_ms")
            car = r.get("car_name") or ""
            value = ms_to_time(int(lap)) if lap else "—"
            lines.append(f"**P{i}** {name} — **{value}**{(' · ' + car) if car else ''}")
        if lines:
            fields.append({"name": _tr(lang, "discord_top3", "Top 3"), "value": "\n".join(lines), "inline": False})

    payload = {
        "username": "WOACC Tracker",
        "embeds": [{
            "title": title,
            "description": desc,
            "color": 3447003,
            "fields": fields,
            "footer": {"text": "WOACC Tracker • Session"},
        }]
    }
    return _post_discord(webhook_url, payload, lang)


def post_license_notification(
    webhook_url: str,
    driver_name: str,
    license_name: str,
    best_time_ms: int,
    session_id: int,
    lang: str = DEFAULT_LANGUAGE,
) -> tuple[bool, str]:
    payload = {
        "username": "WOACC Tracker",
        "embeds": [{
            "title": _tr(lang, "discord_license_title", "🏅 New license achieved"),
            "description": f"**{driver_name or '—'}** ha ottenuto la licenza **{license_name}**",
            "color": 15844367,
            "fields": [
                {"name": _tr(lang, "discord_driver", "Driver"), "value": driver_name or "—", "inline": True},
                {"name": "Licenza", "value": license_name or "—", "inline": True},
                {"name": _tr(lang, "discord_time", "Time"), "value": f"**{ms_to_time(best_time_ms)}**", "inline": True},
                {"name": "Sessione", "value": _tracker_url(session_id), "inline": False},
            ],
            "footer": {"text": "WOACC Tracker • License"},
        }]
    }
    return _post_discord(webhook_url, payload, lang)
