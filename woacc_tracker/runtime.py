"""Tracker engine shared by the desktop and the Windows service."""
import ctypes
import hashlib
import sys
import threading
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer

from .core.config import CONFIG_PATH
from .core.database import Database
from .core.importer import Importer
from .core.monitor import FolderMonitor
from .web.app import create_app


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietLivePollingRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        path = getattr(self, "path", "") or ""
        if "/api/live/leaderboard/" not in path and "/api/live/status" not in path:
            super().log_message(format, *args)


class TrackerRuntime:
    def __init__(self, cfg, log=print, db=None, importer=None):
        self.cfg, self.log = cfg, log
        self.db, self.importer = db, importer
        self.httpd = self.monitor = self.thread = None
        self._mutex = None

    def start(self):
        if self.httpd is not None:
            return
        if sys.platform == "win32":
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CreateMutexW.restype = ctypes.c_void_p
            kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
            name = hashlib.sha256(str(CONFIG_PATH).lower().encode()).hexdigest()[:24]
            self._mutex = kernel.CreateMutexW(None, False, "Global\\WOACCTracker_" + name)
            if not self._mutex:
                raise ctypes.WinError(ctypes.get_last_error())
            if ctypes.get_last_error() == 183:
                self._release_mutex()
                raise OSError("Tracker already running for this configuration")
        try:
            self.db = self.db or Database(self.cfg["database_path"])
            self.db.init_schema()
            self.importer = self.importer or Importer(self.db, self.log)
            app = create_app(self.db, self.cfg)
            host = "0.0.0.0" if self.cfg.get("remote_access") else "127.0.0.1"
            self.httpd = make_server(host, int(self.cfg.get("port", 5055)), app,
                                     server_class=ThreadedWSGIServer, handler_class=QuietLivePollingRequestHandler)
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            self.monitor = FolderMonitor(self.importer, lambda: self.cfg.get("sources", []),
                                         int(self.cfg.get("scan_interval_sec", 10)), self.log, cfg=self.cfg)
            self.monitor.start()
        except Exception:
            self.stop()
            raise

    def _release_mutex(self):
        if self._mutex:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle(self._mutex)
            self._mutex = None

    def stop(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor.wait()
            self.monitor = None
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread:
            self.thread.join()
            self.thread = None
        self._release_mutex()
