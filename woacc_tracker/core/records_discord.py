import json
import urllib.error
import urllib.request
from typing import Optional, List, Dict, Any

from .utils import ms_to_time


def _post_discord(webhook_url: str, payload: Dict[str, Any]) -> tuple[bool, str]:
    webhook_url = (webhook_url or "").strip()

    if not webhook_url:
        return False, "webhook mancante"

    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        return False, "webhook non valido"

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "WOACC-Tracker/1.1"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = getattr(resp, "status", resp.getcode())
            if 200 <= code < 300:
                return True, "annunciato"
            return False, f"Discord HTTP {code}"

    except urllib.error.HTTPError as e:
        return False, f"Discord HTTP {e.code}"

    except urllib.error.URLError as e:
        return False, f"Discord URL Error: {e.reason}"

    except Exception as exc:
        return False, str(exc)


def post_discord_record(
    webhook_url: str,
    announce_name: str,
    track_name: str,
    track_layout: str,
    driver_name: str,
    car_name: str,
    lap_ms: int,
    session_type: str,
    session_datetime: str,
    old_lap_ms: Optional[int] = None,
) -> tuple[bool, str]:

    title = "🏁 Primo record evento" if old_lap_ms is None else "🚀 Nuovo record pista"

    description = (
        f"**{driver_name}** ha segnato un nuovo riferimento su "
        f"**{track_name}{(' / ' + track_layout) if track_layout else ''}**"
    )

    fields = [
        {"name": "Evento", "value": announce_name or "WOACC Tracker", "inline": False},
        {"name": "Pista", "value": f"{track_name}{(' / ' + track_layout) if track_layout else ''}", "inline": True},
        {"name": "Tempo", "value": f"**{ms_to_time(lap_ms)}**", "inline": True},
        {"name": "Pilota", "value": driver_name or "—", "inline": True},
        {"name": "Auto", "value": car_name or "—", "inline": True},
        {"name": "Sessione", "value": session_type or "—", "inline": True},
        {"name": "Data", "value": session_datetime or "—", "inline": True},
    ]

    if old_lap_ms:
        improvement = old_lap_ms - lap_ms
        fields.append({"name": "Record precedente", "value": ms_to_time(old_lap_ms), "inline": True})
        fields.append({"name": "Miglioramento", "value": f"-{improvement / 1000:.3f}s", "inline": True})

    payload = {
        "username": "WOACC Tracker",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 3068284,
                "fields": fields,
                "footer": {
                    "text": "WOACC Tracker • Record Event"
                }
            }
        ]
    }

    return _post_discord(webhook_url, payload)


def post_discord_weekly_recap(
    webhook_url: str,
    announce_name: str,
    period_start: str,
    period_end: str,
    records: List[Dict[str, Any]],
) -> tuple[bool, str]:

    if not records:
        return False, "nessun record da riepilogare"

    lines = []

    for idx, r in enumerate(records[:20], start=1):
        track = r.get("track_name") or "Unknown track"
        layout = r.get("track_layout") or ""
        track_label = f"{track}{(' / ' + layout) if layout else ''}"

        lines.append(
            f"**{idx}. {track_label}**\n"
            f"🏎️ {r.get('driver_name') or '—'} — {r.get('car_name') or '—'}\n"
            f"⏱️ **{ms_to_time(int(r.get('lap_ms') or 0))}** · {r.get('session_type') or '—'} · {r.get('session_datetime') or '—'}"
        )

    extra = ""
    if len(records) > 20:
        extra = f"\n\nAltri record non mostrati: **{len(records) - 20}**"

    payload = {
        "username": "WOACC Tracker",
        "embeds": [
            {
                "title": "📊 Recap settimanale record",
                "description": "\n\n".join(lines) + extra,
                "color": 5814783,
                "fields": [
                    {"name": "Evento", "value": announce_name or "WOACC Tracker", "inline": True},
                    {"name": "Periodo", "value": f"{period_start} → {period_end}", "inline": False},
                    {"name": "Record rilevati", "value": str(len(records)), "inline": True},
                ],
                "footer": {
                    "text": "WOACC Tracker • Weekly Record Recap"
                }
            }
        ]
    }

    return _post_discord(webhook_url, payload)
