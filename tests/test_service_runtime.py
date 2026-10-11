import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import queue
import unittest
from unittest.mock import Mock, patch

from woacc_tracker.runtime import TrackerRuntime
from woacc_tracker.desktop import TrackerDesktop


class ServiceRuntimeTest(unittest.TestCase):
    def test_service_handoff_stops_runtime_off_ui_thread(self):
        desktop = Mock()
        desktop._service_busy = False
        desktop._local_stop_busy = False
        desktop.running = True
        desktop._t.side_effect = lambda key, fallback: fallback
        entered, release = threading.Event(), threading.Event()
        ui_thread = threading.get_ident()
        stop_threads = []
        def stop():
            stop_threads.append(threading.get_ident())
            entered.set()
            release.wait(5)
        desktop.runtime.stop.side_effect = stop
        with patch("woacc_tracker.windows_service.engine_path"), \
             patch("woacc_tracker.desktop.service_status", return_value="not_installed"), \
             patch("woacc_tracker.desktop.messagebox.askyesno", return_value=True), \
             patch("woacc_tracker.desktop.run_service_action") as command:
            try:
                TrackerDesktop._service_action(desktop, "install")
                self.assertTrue(entered.wait(2))
                self.assertTrue(desktop._service_busy)
                self.assertNotEqual(stop_threads, [ui_thread])
                command.assert_not_called()
                desktop._stop_local_tracker.assert_not_called()
                desktop.root.after.assert_called_once_with(100, desktop._poll_service_action)
            finally:
                release.set()
            result = desktop._service_results.get(timeout=5)
            self.assertEqual(result, (None, True, True))
            command.assert_called_once()

    def test_service_completion_is_processed_by_ui_poll(self):
        desktop = Mock()
        desktop._service_results = queue.SimpleQueue()
        desktop._service_results.put(("pending", True, False))
        desktop._t.side_effect = lambda key, fallback: fallback
        TrackerDesktop._poll_service_action(desktop)
        self.assertFalse(desktop.running)
        self.assertIsNone(desktop.runtime)
        desktop._service_action_done.assert_called_once_with("pending", restore=False)

    def test_service_poll_keeps_ui_responsive_while_waiting(self):
        desktop = Mock()
        desktop._service_results = queue.SimpleQueue()
        TrackerDesktop._poll_service_action(desktop)
        desktop.root.after.assert_called_once_with(100, desktop._poll_service_action)
        desktop._service_action_done.assert_not_called()

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
        desktop._stop_local_tracker.assert_called_once_with(close_after=True)
        desktop.stop_tracker.assert_not_called()
        desktop.root.destroy.assert_not_called()

    def test_local_stop_does_not_wait_on_ui_thread(self):
        desktop = Mock()
        desktop._local_stop_busy = False
        desktop._close_after_stop = False
        desktop._t.side_effect = lambda key, fallback: fallback
        entered, release = threading.Event(), threading.Event()
        threads = []
        def stop():
            threads.append(threading.get_ident())
            entered.set()
            release.wait(5)
        desktop.runtime.stop.side_effect = stop
        try:
            TrackerDesktop._stop_local_tracker(desktop, close_after=True)
            self.assertTrue(entered.wait(2))
            self.assertNotEqual(threads, [threading.get_ident()])
            self.assertTrue(desktop._local_stop_busy)
            desktop.root.destroy.assert_not_called()
            desktop.root.after.assert_called_once_with(100, desktop._poll_local_stop)
        finally:
            release.set()
        self.assertIsNone(desktop._local_stop_results.get(timeout=5))
        desktop._local_stop_results.put(None)
        TrackerDesktop._poll_local_stop(desktop)
        self.assertFalse(desktop._local_stop_busy)
        self.assertIsNone(desktop.runtime)
        desktop._local_stop_done.assert_called_once()

    def test_close_waits_for_completed_local_stop(self):
        desktop = Mock()
        desktop._close_after_stop = True
        desktop._t.side_effect = lambda key, fallback: fallback
        TrackerDesktop._local_stop_done(desktop)
        self.assertFalse(desktop.running)
        desktop.root.destroy.assert_called_once()

    def test_start_is_ignored_until_local_stop_finishes(self):
        desktop = Mock()
        desktop._service_busy = False
        desktop._local_stop_busy = True
        TrackerDesktop.start_tracker(desktop)
        desktop.save_settings.assert_not_called()

    def test_failed_stop_does_not_close_or_discard_runtime(self):
        desktop = Mock()
        runtime = desktop.runtime
        desktop._local_stop_results = queue.SimpleQueue()
        desktop._local_stop_results.put("stop failed")
        desktop._close_after_stop = True
        with patch("woacc_tracker.desktop.messagebox.showerror") as error:
            TrackerDesktop._poll_local_stop(desktop)
        self.assertIs(desktop.runtime, runtime)
        self.assertFalse(desktop._close_after_stop)
        desktop.root.destroy.assert_not_called()
        error.assert_called_once()

    def test_installed_service_prevents_desktop_autostart(self):
        desktop = Mock()
        desktop.cfg = {"auto_start_tracker": True}
        with patch("woacc_tracker.desktop.service_status", return_value="running"):
            TrackerDesktop._auto_start_tracker_if_enabled(desktop)
        desktop.start_tracker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
