import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(os.environ["WOACC_CONFIG_PATH"]).resolve() if os.getenv("WOACC_CONFIG_PATH") else Path(os.getenv("APPDATA", Path.home())) / "WOACC_Tracker" / "config.json"
APP_DIR = CONFIG_PATH.parent
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
    "auto_start_tracker": True,
    "scan_interval_sec": 10,
    "language": "it",
    "database_path": str(DB_PATH),
    "tracker_mode": "evo",
    "default_sim": "evo",
    "evo_manager_path": "",
    "accweb_path": "",
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
    cfg["sources"] = [dict(source, sim=source.get("sim") or "evo") for source in (cfg.get("sources") or [])]
    if cfg.get("tracker_mode") not in {"evo", "acc", "both"}:
        cfg["tracker_mode"] = "evo"
    if cfg.get("default_sim") not in {"evo", "acc"}:
        cfg["default_sim"] = "evo"
    if "woacc_api_enabled" not in cfg:
        cfg["woacc_api_enabled"] = True
    cfg["woacc_api_key"] = (cfg.get("woacc_api_key") or DEFAULT_WOACC_API_KEY).strip()
    return _merge_theme(cfg)


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_app_dir()
    _merge_theme(cfg)
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=APP_DIR, delete=False) as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        temporary = Path(f.name)
    try:
        os.replace(temporary, CONFIG_PATH)
    finally:
        temporary.unlink(missing_ok=True)
