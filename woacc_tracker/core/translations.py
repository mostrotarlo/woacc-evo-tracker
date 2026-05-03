
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

DEFAULT_LANGUAGE = "it"
I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"


def available_languages() -> Dict[str, str]:
    langs: Dict[str, str] = {}
    if not I18N_DIR.exists():
        return {DEFAULT_LANGUAGE: "Italiano"}
    for path in sorted(I18N_DIR.glob("*.json")):
        code = path.stem.lower()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            langs[code] = data.get("lang_name") or code.upper()
        except Exception:
            langs[code] = code.upper()
    return langs or {DEFAULT_LANGUAGE: "Italiano"}


@lru_cache(maxsize=32)
def load_vocabulary(lang: str) -> Dict[str, Any]:
    lang = (lang or DEFAULT_LANGUAGE).lower()
    base = _load_file(DEFAULT_LANGUAGE)
    if lang != DEFAULT_LANGUAGE:
        base.update(_load_file(lang))
    return base


def _load_file(lang: str) -> Dict[str, Any]:
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def pick_language(request, cfg: Dict[str, Any]) -> str:
    available = available_languages()
    requested = (request.args.get("lang") or "").strip().lower()
    if requested in available:
        return requested
    cookie_lang = (request.cookies.get("woacc_lang") or "").strip().lower()
    if cookie_lang in available:
        return cookie_lang
    cfg_lang = (cfg.get("language") or DEFAULT_LANGUAGE).strip().lower()
    return cfg_lang if cfg_lang in available else DEFAULT_LANGUAGE
