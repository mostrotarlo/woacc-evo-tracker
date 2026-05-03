import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def key_to_str(k: Any) -> str:
    if isinstance(k, dict):
        return f"{k.get('a','')}:{k.get('b','')}"
    return str(k or "")


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def make_server_key(server_name: str, track_name: str) -> str:
    return f"{normalize_text(server_name)}::{normalize_text(track_name)}"


def ms_to_time(ms: Optional[int]) -> str:
    if not ms or ms <= 0:
        return "—"
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    if minutes:
        return f"{minutes}:{seconds:02d}.{millis:03d}"
    return f"{seconds}.{millis:03d}"


def format_gap(ms: Optional[int]) -> str:
    if ms is None:
        return "—"
    if ms == 0:
        return "—"
    return f"+{ms/1000:.3f}"


def parse_datetime_from_filename(path: str) -> str:
    name = Path(path).name
    m = re.search(r"(20\d{6})[_-](\d{6})", name)
    if m:
        try:
            return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").isoformat(timespec="seconds")
        except ValueError:
            pass
    try:
        ts = Path(path).stat().st_mtime
        return datetime.fromtimestamp(ts).isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")


def display_driver_name(driver: Dict[str, Any]) -> str:
    # Per la v0.1 usiamo first + last, e fallback nickname. È più leggibile nelle classifiche.
    first = (driver.get("first_name") or "").strip()
    last = (driver.get("last_name") or "").strip()
    nick = (driver.get("nickname") or "").strip()
    name = " ".join([p for p in [first, last] if p]).strip()
    return name or nick or driver.get("player_id") or "Unknown driver"
