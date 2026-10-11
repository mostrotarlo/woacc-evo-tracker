import json
from pathlib import Path
from .utils import json_file_encoding


def _read_json(path: Path) -> dict:
    try:
        with path.open("r", encoding=json_file_encoding(path)) as stream:
            value = json.load(stream)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def discover_managed_sources(sim: str, manager_path: str) -> list[dict]:
    root = Path(manager_path).expanduser()
    if root.is_file():
        root = root.parent
    if sim == "evo":
        candidates = (root / "servers").glob("*/server.json")
    elif sim == "acc":
        candidates = (root / "config").glob("*/accwebConfig.json")
    else:
        return []

    sources = []
    for marker in sorted(candidates):
        server_dir = marker.parent
        if sim == "evo":
            info = _read_json(marker)
            results = Path(info.get("results_path") or server_dir / "result")
            if not results.is_absolute():
                results = server_dir / results
            log_path = server_dir / "serverConfig" / "Assetto Corsa EVO Server.txt"
            name = str(info.get("name") or server_dir.name).strip()
        else:
            settings = _read_json(server_dir / "settings.json")
            results = server_dir / "results"
            log_path = server_dir / "log" / "server.log"
            name = str(settings.get("serverName") or server_dir.name).strip()
        sources.append({
            "name": name,
            "path": str(results.resolve()),
            "sim": sim,
            "enabled": True,
            "managed_by": "evo_manager" if sim == "evo" else "accweb",
            "managed_id": server_dir.name,
            "managed_name": name,
            "server_log_path": str(log_path.resolve()) if log_path.exists() else "",
            "live_leaderboard_enabled": sim == "acc",
            "announce_records": False,
            "announce_name": name,
        })
    return sources


def sync_managed_sources(cfg: dict) -> bool:
    sources = cfg.setdefault("sources", [])
    changed = False
    for sim, key in (("evo", "evo_manager_path"), ("acc", "accweb_path")):
        root = cfg.get(key) or ""
        if not root:
            continue
        manager_root = Path(root).expanduser()
        if manager_root.is_file():
            manager_root = manager_root.parent
        expected = manager_root / ("servers" if sim == "evo" else "config")
        if not expected.is_dir():
            continue
        found = discover_managed_sources(sim, root)
        by_path = {str(Path(src["path"]).resolve()).lower(): src for src in found}
        manager = "evo_manager" if sim == "evo" else "accweb"
        retained = []
        for source in sources:
            source_path = str(Path(source.get("path") or "").resolve()).lower()
            if not source.get("managed_by") and (source.get("sim") or "evo") == sim and source_path in by_path:
                discovered = by_path[source_path]
                source["managed_by"] = manager
                source["managed_id"] = discovered["managed_id"]
                source["managed_name"] = discovered["name"]
                if not source.get("server_log_path"):
                    source["server_log_path"] = discovered["server_log_path"]
                changed = True
            if source.get("managed_by") != manager:
                retained.append(source)
                continue
            updated = by_path.pop(source_path, None)
            if updated is None:
                changed = True
                continue
            if source.get("name") == source.get("managed_name", source.get("name")) and source.get("name") != updated["name"]:
                source["name"] = updated["name"]
                changed = True
            source["managed_name"] = updated["name"]
            if not source.get("server_log_path") and updated["server_log_path"]:
                source["server_log_path"] = updated["server_log_path"]
                changed = True
            for field in ("managed_id", "sim"):
                if source.get(field) != updated[field]:
                    source[field] = updated[field]
                    changed = True
            retained.append(source)
        if by_path:
            existing_paths = {str(Path(src.get("path") or "").resolve()).lower() for src in retained}
            additions = [src for path, src in by_path.items() if path not in existing_paths]
            if additions:
                retained.extend(additions)
                changed = True
        sources = retained
    if changed:
        cfg["sources"] = sources
    return changed
