import json
import os
from pathlib import Path
from typing import Any, Dict

APP_DIR = Path(os.getenv("APPDATA", Path.home())) / "WOACC_Tracker"
CONFIG_PATH = APP_DIR / "config.json"
DB_PATH = APP_DIR / "woacc_tracker.db"

# Shared bridge key used by ACC_JSON_Monitor_Plus 2.
# The API can still be disabled from the desktop app with woacc_api_enabled=false.
DEFAULT_WOACC_API_KEY = "WOACC-EVO-BRIDGE-V13-ACCJSONMONITORPLUS2"

DEFAULT_CONFIG: Dict[str, Any] = {
    "community_name": "WOACC Tracker",
    "host_label": "",
    "port": 5055,
    "remote_access": False,
    "public_url": "",
    "base_path": "",
    "password_enabled": False,
    "password_hash": "",
    "session_timeout_hours": 24,
    "woacc_api_enabled": True,
    "woacc_api_key": DEFAULT_WOACC_API_KEY,
    "woacc_main_url": "https://woacc.zapto.org/",
    "woacc_discord_url": "https://discord.com/channels/@me",
    "woacc_discord_contact": "Fabio / WOACC",
    "woacc_request_message": "Ciao Fabio, vorrei collegare il mio WOACC Tracker EVO al WOACC globale. Indirizzo tracker da aggiungere: ",
    "weekly_recap_enabled": False,
    "weekly_recap_webhook_url": "",
    "weekly_recap_started_at": "",
    "weekly_recap_last_sent_at": "",
    "scan_interval_sec": 10,
    "language": "it",
    "database_path": str(DB_PATH),
    "sources": [],
    "theme": {
        "font_family": "Segoe UI, Arial, sans-serif",
        "font_size": 16,
        "background": "#0b0f14",
        "card": "#141b24",
        "card2": "#101720",
        "line": "#263241",
        "text": "#e8eef6",
        "muted": "#93a4b8",
        "accent": "#2fd17c",
        "danger": "#ff5c5c",
        "warn": "#f7c948"
    }
}


def ensure_app_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def _merge_theme(cfg: Dict[str, Any]) -> Dict[str, Any]:
    theme = DEFAULT_CONFIG["theme"].copy()
    if isinstance(cfg.get("theme"), dict):
        theme.update(cfg.get("theme") or {})
    cfg["theme"] = theme
    return cfg


def load_config() -> Dict[str, Any]:
    ensure_app_dir()
    if not CONFIG_PATH.exists():
        cfg = DEFAULT_CONFIG.copy()
        cfg["theme"] = DEFAULT_CONFIG["theme"].copy()
        save_config(cfg)
        return cfg
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(data)
    if "woacc_api_enabled" not in cfg:
        cfg["woacc_api_enabled"] = True
    # v13 definitive: ACC_JSON_Monitor_Plus 2 uses this shared bridge key.
    cfg["woacc_api_key"] = DEFAULT_WOACC_API_KEY
    return _merge_theme(cfg)


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_app_dir()
    _merge_theme(cfg)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
