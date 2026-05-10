import json
import urllib.error
import urllib.request
from typing import Optional, List, Dict, Any

from .utils import ms_to_time
from .translations import DEFAULT_LANGUAGE, load_vocabulary


def _tr(lang: str, key: str, default: str) -> str:
    vocab = load_vocabulary((lang or DEFAULT_LANGUAGE).lower())
    return str(vocab.get(key, default))


def _post_discord(webhook_url: str, payload: Dict[str, Any], lang: str = DEFAULT_LANGUAGE) -> tuple[bool, str]:
    webhook_url = (webhook_url or "").strip()

    if not webhook_url:
        return False, _tr(lang, "discord_missing_webhook", "missing webhook")

    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        return False, _tr(lang, "discord_invalid_webhook", "invalid webhook")

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
                return True, _tr(lang, "discord_announced", "announced")
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
    lang: str = DEFAULT_LANGUAGE,
) -> tuple[bool, str]:

    track_label = f"{track_name}{(' / ' + track_layout) if track_layout else ''}"
    title = _tr(lang, "discord_first_record_title", "🏁 First event record") if old_lap_ms is None else _tr(lang, "discord_new_record_title", "🚀 New track record")

    description = _tr(
        lang,
        "discord_record_description",
        "**{driver}** set a new benchmark on **{track}**"
    ).format(driver=driver_name, track=track_label)

    fields = [
        {"name": _tr(lang, "discord_event", "Event"), "value": announce_name or "WOACC Tracker", "inline": False},
        {"name": _tr(lang, "discord_track", "Track"), "value": track_label, "inline": True},
        {"name": _tr(lang, "discord_time", "Time"), "value": f"**{ms_to_time(lap_ms)}**", "inline": True},
        {"name": _tr(lang, "discord_driver", "Driver"), "value": driver_name or "—", "inline": True},
        {"name": _tr(lang, "discord_car", "Car"), "value": car_name or "—", "inline": True},
        {"name": _tr(lang, "discord_session", "Session"), "value": session_type or "—", "inline": True},
        {"name": _tr(lang, "discord_date", "Date"), "value": session_datetime or "—", "inline": True},
    ]

    if old_lap_ms:
        improvement = old_lap_ms - lap_ms
        fields.append({"name": _tr(lang, "discord_previous_record", "Previous record"), "value": ms_to_time(old_lap_ms), "inline": True})
        fields.append({"name": _tr(lang, "discord_improvement", "Improvement"), "value": f"-{improvement / 1000:.3f}s", "inline": True})

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

    return _post_discord(webhook_url, payload, lang)


def post_discord_weekly_recap(
    webhook_url: str,
    announce_name: str,
    period_start: str,
    period_end: str,
    records: List[Dict[str, Any]],
    lang: str = DEFAULT_LANGUAGE,
) -> tuple[bool, str]:

    if not records:
        return False, _tr(lang, "discord_no_records_recap", "no records to recap")

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
        extra = "\n\n" + _tr(lang, "discord_more_records", "Other records not shown: **{count}**").format(count=len(records) - 20)

    payload = {
        "username": "WOACC Tracker",
        "embeds": [
            {
                "title": _tr(lang, "discord_weekly_recap_title", "📊 Weekly record recap"),
                "description": "\n\n".join(lines) + extra,
                "color": 5814783,
                "fields": [
                    {"name": _tr(lang, "discord_event", "Event"), "value": announce_name or "WOACC Tracker", "inline": True},
                    {"name": _tr(lang, "discord_period", "Period"), "value": f"{period_start} → {period_end}", "inline": False},
                    {"name": _tr(lang, "discord_records_detected", "Records detected"), "value": str(len(records)), "inline": True},
                ],
                "footer": {
                    "text": "WOACC Tracker • Weekly Record Recap"
                }
            }
        ]
    }

    return _post_discord(webhook_url, payload, lang)
