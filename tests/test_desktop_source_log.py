import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from woacc_tracker.desktop import TrackerDesktop


class DesktopSourceLogTest(unittest.TestCase):
    def test_evo_log_detection_and_manual_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = root / "result"
            results.mkdir()
            log = root / "serverConfig" / "Assetto Corsa EVO Server.txt"
            log.parent.mkdir()
            log.touch()
            for detected in (True, False):
                with self.subTest(detected=detected):
                    if not detected:
                        log.unlink()
                    desktop = Mock()
                    desktop.cfg = {}
                    desktop._t.side_effect = lambda key, fallback: fallback
                    with patch("woacc_tracker.desktop.filedialog.askdirectory", return_value=str(results)), \
                         patch("woacc_tracker.desktop.simpledialog.askstring", return_value="Test"), \
                         patch("woacc_tracker.desktop.filedialog.askopenfilename", return_value="manual.txt") as select, \
                         patch("woacc_tracker.desktop.save_config"):
                        TrackerDesktop.add_source(desktop, "evo")
                    expected = str(log) if detected else "manual.txt"
                    self.assertEqual(desktop.cfg["sources"][0]["server_log_path"], expected)
                    desktop._offer_server_log_sync.assert_called_once_with(expected)
                    if detected:
                        select.assert_not_called()
                    else:
                        select.assert_called_once()

    def test_acc_log_detection_and_manual_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = root / "result"
            results.mkdir()
            log = root / "log" / "server.log"
            log.parent.mkdir()
            log.touch()
            for detected in (True, False):
                with self.subTest(detected=detected):
                    if not detected:
                        log.unlink()
                    desktop = Mock()
                    desktop.cfg = {}
                    desktop._t.side_effect = lambda key, fallback: fallback
                    with patch("woacc_tracker.desktop.filedialog.askdirectory", return_value=str(results)), \
                         patch("woacc_tracker.desktop.simpledialog.askstring", return_value="Test"), \
                         patch("woacc_tracker.desktop.filedialog.askopenfilename", return_value="manual.log") as select, \
                         patch("woacc_tracker.desktop.save_config"):
                        TrackerDesktop.add_source(desktop, "acc")
                    self.assertEqual(desktop.cfg["sources"][0]["server_log_path"], str(log) if detected else "manual.log")
                    desktop._offer_server_log_sync.assert_not_called()
                    self.assertEqual(select.call_count, 0 if detected else 1)


if __name__ == "__main__":
    unittest.main()
