import threading
import time
from pathlib import Path
from typing import Callable, Dict, List

from .importer import Importer
from .source_discovery import sync_managed_sources
from .config import save_config


class FolderMonitor:
    def __init__(self, importer: Importer, sources_getter: Callable[[], List[Dict]], interval_sec: int = 10, log: Callable[[str], None] = print, cfg: dict | None = None):
        self.importer = importer
        self.sources_getter = sources_getter
        self.interval_sec = max(2, int(interval_sec or 10))
        self.log = log
        self.cfg = cfg
        self._stop = threading.Event()
        self._thread = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def wait(self) -> None:
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()

    def scan_once(self) -> None:
        if self.cfg is not None and sync_managed_sources(self.cfg):
            save_config(self.cfg)
        mode = (self.cfg or {}).get("tracker_mode", "evo")
        for source in self.sources_getter():
            if self._stop.is_set():
                break
            if not source.get("enabled", True):
                continue
            if mode != "both" and (source.get("sim") or "evo") != mode:
                continue
            path = Path(source.get("path", ""))
            name = source.get("name") or path.name
            stats = self.importer.import_folder(path, name, source)
            if stats["found"] or stats["imported"] or stats["errors"]:
                self.log(f"Scansione {path}: trovati {stats['found']}, importati {stats['imported']}, saltati {stats['skipped']}, errori {stats['errors']}")
                
        self.importer.flush_record_announcements()
        self.importer.check_weekly_recaps()

    def _loop(self) -> None:
        self.log("Monitoraggio cartelle avviato")
        while not self._stop.is_set():
            try:
                self.scan_once()
            except Exception as exc:
                self.log(f"Errore monitoraggio: {exc}")
            self._stop.wait(self.interval_sec)
        self.log("Monitoraggio cartelle fermato")
