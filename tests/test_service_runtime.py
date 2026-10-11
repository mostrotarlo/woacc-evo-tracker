import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from woacc_tracker.runtime import TrackerRuntime
from woacc_tracker.desktop import TrackerDesktop


class ServiceRuntimeTest(unittest.TestCase):
    def test_explicit_configuration_path_preserves_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            database = str(Path(directory) / "existing.db")
            path.write_text(json.dumps({"database_path": database}), encoding="utf-8")
            env = dict(os.environ, WOACC_CONFIG_PATH=str(path))
            result = subprocess.run([sys.executable, "-c",
                "from woacc_tracker.core.config import load_config,CONFIG_PATH; import json; print(json.dumps([str(CONFIG_PATH),load_config()['database_path']]))"],
                env=env, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), [str(path.resolve()), database])

    def test_runtime_starts_and_stops_shared_components(self):
        database, importer = Mock(), Mock()
        cfg = {"database_path": "unused", "port": 5055}
        with patch("woacc_tracker.runtime.sys.platform", "test"), \
             patch("woacc_tracker.runtime.create_app"), \
             patch("woacc_tracker.runtime.make_server") as server, \
             patch("woacc_tracker.runtime.FolderMonitor") as monitor:
            runtime = TrackerRuntime(cfg, db=database, importer=importer)
            runtime.start()
            runtime.stop()
            database.init_schema.assert_called_once()
            monitor.return_value.start.assert_called_once()
            monitor.return_value.stop.assert_called_once()
            monitor.return_value.wait.assert_called_once()
            server.return_value.shutdown.assert_called_once()
            server.return_value.server_close.assert_called_once()
            self.assertIsNone(runtime.httpd)

    def test_runtime_releases_resources_on_start_failure(self):
        with patch("woacc_tracker.runtime.sys.platform", "test"), \
             patch("woacc_tracker.runtime.create_app"), \
             patch("woacc_tracker.runtime.make_server", side_effect=OSError("busy")):
            runtime = TrackerRuntime({"database_path": "unused"}, db=Mock(), importer=Mock())
            with self.assertRaises(OSError):
                runtime.start()
            self.assertIsNone(runtime.httpd)

    def test_closing_desktop_does_not_stop_service(self):
        desktop = Mock()
        desktop._service_busy = False
        TrackerDesktop.close(desktop)
        desktop._stop_local_tracker.assert_called_once()
        desktop.stop_tracker.assert_not_called()
        desktop.root.destroy.assert_called_once()

    def test_installed_service_prevents_desktop_autostart(self):
        desktop = Mock()
        desktop.cfg = {"auto_start_tracker": True}
        with patch("woacc_tracker.desktop.service_status", return_value="running"):
            TrackerDesktop._auto_start_tracker_if_enabled(desktop)
        desktop.start_tracker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
