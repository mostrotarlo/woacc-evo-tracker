"""Standalone service executable. Configuration is selected before engine imports."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import threading

import servicemanager
import win32service
import win32serviceutil
import winreg

from woacc_tracker.windows_service import SERVICE_NAME, PARAMETERS_KEY, service_config_path


class TrackerService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = "WOACC Tracker"
    _svc_description_ = "ACC and EVO results monitoring, live timing and web API."

    def __init__(self, args):
        super().__init__(args)
        self.stopped = threading.Event()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stopped.set()

    def SvcDoRun(self):
        path = service_config_path()
        if not path.is_file():
            raise FileNotFoundError(f"Registered configuration not found: {path}")
        settings = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict) or not settings.get("database_path") or not Path(settings["database_path"]).is_absolute():
            raise ValueError("The service requires an explicit absolute database path")
        os.environ["WOACC_CONFIG_PATH"] = str(path)
        os.chdir(path.parent)
        logger = logging.getLogger("woacc.service")
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(path.parent / "service.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        from woacc_tracker.core.config import load_config
        from woacc_tracker.runtime import TrackerRuntime
        runtime = TrackerRuntime(load_config(), logger.info)
        try:
            runtime.start()
            logger.info("WOACC Tracker service started")
            self.stopped.wait()
        except Exception:
            logger.exception("Tracker service failed")
            raise
        finally:
            # Report pending periodically while a current import finishes.
            done = threading.Event()
            def stop_runtime():
                try:
                    runtime.stop()
                finally:
                    done.set()
            threading.Thread(target=stop_runtime).start()
            while not done.wait(2):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, waitHint=10000)
            logger.info("WOACC Tracker service stopped")
            handler.close()


def manage(action, path):
    executable = str(Path(sys.executable).resolve())
    if action == "install":
        if not getattr(sys, "frozen", False):
            raise RuntimeError("Install the compiled engine, not the Python script")
        if not path.is_file():
            raise FileNotFoundError(path)
        win32serviceutil.InstallService(
            None, SERVICE_NAME, TrackerService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START, exeName=executable,
            description=TrackerService._svc_description_, delayedstart=True,
        )
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, PARAMETERS_KEY) as key:
                winreg.SetValueEx(key, "ConfigPath", 0, winreg.REG_SZ, str(path))
            win32serviceutil.StartService(SERVICE_NAME)
            win32serviceutil.WaitForServiceStatus(SERVICE_NAME, win32service.SERVICE_RUNNING, 60)
        except Exception:
            try:
                if win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1] != win32service.SERVICE_STOPPED:
                    win32serviceutil.StopService(SERVICE_NAME)
                    win32serviceutil.WaitForServiceStatus(SERVICE_NAME, win32service.SERVICE_STOPPED, 120)
                win32serviceutil.RemoveService(SERVICE_NAME)
            except Exception:
                logging.exception("Unable to roll back service installation")
            raise
    elif action in {"stop", "remove", "restart"}:
        if win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1] != win32service.SERVICE_STOPPED:
            win32serviceutil.StopService(SERVICE_NAME)
            win32serviceutil.WaitForServiceStatus(SERVICE_NAME, win32service.SERVICE_STOPPED, 120)
        if action == "remove":
            win32serviceutil.RemoveService(SERVICE_NAME)
        elif action == "restart":
            win32serviceutil.StartService(SERVICE_NAME)
            win32serviceutil.WaitForServiceStatus(SERVICE_NAME, win32service.SERVICE_RUNNING, 60)
    elif action == "start":
        win32serviceutil.StartService(SERVICE_NAME)
        win32serviceutil.WaitForServiceStatus(SERVICE_NAME, win32service.SERVICE_RUNNING, 60)


def main():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TrackerService)
        servicemanager.StartServiceCtrlDispatcher()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=("install", "start", "stop", "restart", "remove"), required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        manage(args.action, args.config.resolve())
    except Exception:
        logging.basicConfig(filename=args.config.parent / "service-control.log", level=logging.ERROR)
        logging.exception("Service control failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
