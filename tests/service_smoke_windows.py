"""Optional elevated integration test, isolated from the production tracker."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from woacc_tracker.windows_service import engine_path, service_status, service_config_path, SERVICE_NAME


def main():
    if service_status() != "not_installed":
        raise RuntimeError("An existing tracker service must not be changed by this test")
    folder = ROOT / "backups" / "service_smoke"
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / "config.json"
    config.write_text(json.dumps({"database_path": str(folder / "test.db"),
        "port": 5056, "sources": [], "tracker_mode": "both", "auto_start_tracker": False}), encoding="utf-8")
    executable = engine_path()
    report = {}
    def action(name):
        subprocess.run([str(executable), "--action", name, "--config", str(config)], check=True)
    def ready():
        for _ in range(60):
            try:
                with urllib.request.urlopen("http://127.0.0.1:5056/", timeout=2) as response:
                    if response.status == 200:
                        return
            except OSError:
                time.sleep(1)
        raise RuntimeError("Service did not answer on the isolated test port")
    try:
        action("install")
        ready()
        report["started"] = service_status() == "running"
        report["explicit_config"] = service_config_path() == config.resolve()
        import win32service
        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        handle = win32service.OpenService(manager, SERVICE_NAME, win32service.SERVICE_QUERY_CONFIG)
        try:
            report["automatic_start"] = win32service.QueryServiceConfig(handle)[1] == win32service.SERVICE_AUTO_START
        finally:
            win32service.CloseServiceHandle(handle)
            win32service.CloseServiceHandle(manager)
        env = dict(os.environ, WOACC_CONFIG_PATH=str(config))
        duplicate = subprocess.run([sys.executable, "-c",
            "from woacc_tracker.core.config import load_config; from woacc_tracker.runtime import TrackerRuntime; TrackerRuntime(load_config()).start()"],
            cwd=ROOT, env=env, capture_output=True, text=True)
        report["duplicate_blocked"] = duplicate.returncode != 0 and (
            "already running" in duplicate.stderr or "[WinError 5]" in duplicate.stderr)
        (folder / "duplicate-error.txt").write_text(duplicate.stderr, encoding="utf-8")
        action("stop")
        report["stopped"] = service_status() == "stopped"
        action("start")
        ready()
        report["restarted"] = service_status() == "running"
    finally:
        if service_status() != "not_installed":
            action("remove")
        report["removed"] = service_status() == "not_installed"
        (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not all(report.values()):
        raise RuntimeError(str(report))


if __name__ == "__main__":
    main()
