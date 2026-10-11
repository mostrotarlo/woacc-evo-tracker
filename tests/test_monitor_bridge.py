import importlib.util
import json
import logging
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch


PROVIDER_PATH = Path(__file__).resolve().parents[1] / "integration" / "WOACC_Unified_Monitor" / "providers" / "evo_provider.py"
ACC_PROVIDER_PATH = PROVIDER_PATH.with_name("acc_provider.py")


class State:
    def __init__(self):
        self.hashes = {}
        self.data = {"processed_hashes": self.hashes}

    def hash_seen(self, key):
        return key in self.hashes

    def mark_hash(self, key, **values):
        self.hashes[key] = values

    def mark_url(self, *args, **kwargs):
        pass

    def save(self):
        pass


class BridgeMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = {}
        stubs = {
            "requests": types.ModuleType("requests"),
            "urllib3": types.ModuleType("urllib3"),
            "providers": types.ModuleType("providers"),
            "providers.evo_converter2": types.ModuleType("providers.evo_converter2"),
            "providers.acc_provider": types.ModuleType("providers.acc_provider"),
            "bs4": types.ModuleType("bs4"),
            "chardet": types.ModuleType("chardet"),
        }
        stubs["urllib3"].exceptions = types.SimpleNamespace(InsecureRequestWarning=Warning)
        stubs["urllib3"].disable_warnings = lambda *_: None
        stubs["providers.evo_converter2"].convert_evo_json = lambda data, *_: {"laps": []}
        cls.evo_outputs = []
        def save_evo(data, folder):
            cls.evo_outputs.append(data)
            return str(Path(folder) / "evo.json")
        stubs["providers.evo_converter2"].save_converted_json = save_evo

        def convert_acc(raw, folder, conditions=None):
            self = cls
            self.acc_raw_paths.append(Path(raw))
            Path(folder).mkdir(parents=True, exist_ok=True)
            output = Path(folder) / "acc.json"
            output.write_text(json.dumps({"conditions": conditions or {}}), encoding="utf-8")
            return str(output)

        stubs["providers.acc_provider"].correct_json_format = convert_acc
        stubs["bs4"].BeautifulSoup = lambda *_: None
        stubs["chardet"].detect = lambda *_: {"encoding": "utf-8"}
        cls.acc_raw_paths = []
        for name, stub in stubs.items():
            cls.modules[name] = sys.modules.get(name)
            sys.modules[name] = stub
        spec = importlib.util.spec_from_file_location("bridge_under_test", PROVIDER_PATH)
        cls.provider = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.provider)
        acc_spec = importlib.util.spec_from_file_location("acc_converter_under_test", ACC_PROVIDER_PATH)
        cls.acc_provider = importlib.util.module_from_spec(acc_spec)
        acc_spec.loader.exec_module(cls.acc_provider)

    @classmethod
    def tearDownClass(cls):
        for name, original in cls.modules.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = State()
        self.monitor = self.provider.EvoTrackerMonitor(
            base_url="https://example.test/tracker",
            results_dir=str(Path(self.temp.name) / "results"),
            session_json_dir=str(Path(self.temp.name) / "evo_out"),
            acc_output_dir=str(Path(self.temp.name) / "session_jsons"),
            state_store=self.state,
            logger=logging.getLogger("bridge_test"),
            verify_ssl=True,
            user_agent="bridge-test",
            stop_event=threading.Event(),
            batch_size=2,
            check_interval_sec=5,
            sleep_between_downloads_sec=0,
            api_key="one-key",
            acc_backfill_existing=True,
        )
        self.assertEqual(self.monitor.headers["X-WOACC-API-Key"], "one-key")
        self.acc_raw_paths.clear()
        self.evo_outputs.clear()

    def _run(self, dual):
        urls = []
        def api(url, timeout=45):
            urls.append(url)
            if url.endswith("/ping"):
                return {"ok": True, "supported_sims": ["evo", "acc"] if dual else []}
            if "sim=acc" in url:
                return {"items": [{"sim": "acc", "file_hash": "same", "session_id": 2,
                                   "session_datetime": "2026-10-10T09:10:11", "download_url": "/api/woacc/session/2/original.json",
                                   "conditions": {"initial_global_wetness": 0}}]}
            return {"items": [{"file_hash": "same", "session_id": 1,
                               "download_url": "/api/woacc/session/1/original.json",
                               "conditions": {"ambient_temperature_c": 23.4, "track_grip": 0.98}}]}

        with patch.object(self.monitor, "_api_get_json", side_effect=api), patch.object(
            self.monitor, "_download_bytes", return_value=b"{}"
        ):
            self.monitor.tick_once()
        return urls

    def test_legacy_tracker_only_imports_evo(self):
        urls = self._run(False)
        self.assertFalse(any("sim=acc" in url for url in urls))
        self.assertEqual(set(self.state.hashes), {"evo:same"})

    def test_both_sims_get_distinct_state_and_output(self):
        urls = self._run(True)
        self.assertTrue(any("sim=acc" in url for url in urls))
        self.assertEqual(set(self.state.hashes), {"evo:same", "sha256:same"})
        self.assertEqual(len(self.acc_raw_paths), 1)
        self.assertTrue(self.acc_raw_paths[0].name.startswith("261010_091011_"))
        self.assertTrue((Path(self.temp.name) / "session_jsons" / "acc.json").exists())
        self.assertEqual(json.loads((Path(self.temp.name) / "session_jsons" / "acc.json").read_text())["conditions"]["initial_global_wetness"], 0)
        self.assertEqual(self.evo_outputs[0]["conditions"]["track_grip"], 0.98)
        self.assertEqual(self.evo_outputs[0]["__conditions_source"], "evo_server_log")
        self.assertTrue((Path(self.temp.name) / "results" / "ACC_example.test_tracker" / "raw").exists())

    def test_first_acc_scan_baselines_existing_sessions(self):
        self.monitor.acc_backfill_existing = False
        self._run(True)
        self.assertEqual(self.state.hashes["sha256:same"]["status"], "baseline")
        self.assertTrue(any(key.startswith("acc-api-baseline:") for key in self.state.hashes))
        self.assertFalse(self.acc_raw_paths)

    def test_late_import_of_old_acc_session_stays_in_baseline(self):
        self.monitor.acc_backfill_existing = False
        self._run(True)
        new_hash = "late-old-session"
        def api(url, timeout=45):
            if url.endswith("/ping"):
                return {"ok": True, "supported_sims": ["evo", "acc"]}
            if "sim=acc" in url:
                return {"items": [{"sim": "acc", "file_hash": new_hash, "session_id": 3,
                                   "session_datetime": "2026-10-07T10:00:00",
                                   "imported_at": "2026-10-10T11:00:00",
                                   "download_url": "/api/woacc/session/3/original.json"}]}
            return {"items": []}
        with patch.object(self.monitor, "_api_get_json", side_effect=api):
            self.monitor.tick_once()
        self.assertEqual(self.state.hashes[f"sha256:{new_hash}"]["status"], "baseline")
        self.assertFalse(self.acc_raw_paths)

    def test_acc_api_skips_raw_file_already_imported_by_acc_hosting(self):
        self.state.mark_hash("sha256:same", status="ok", first_seen="", output_file="existing.json")
        self._run(True)
        self.assertFalse(self.acc_raw_paths)
        self.assertEqual(self.state.hashes["sha256:same"]["output_file"], "existing.json")

    def test_acc_conversion_preserves_steam_ids_for_codrivers(self):
        payload = {
            "sessionType": "FP", "serverName": "Test", "trackName": "monza",
            "sessionResult": {"isWetSession": 1, "leaderBoardLines": [{
                "car": {"carId": 0, "carModel": 31, "raceNumber": 42, "drivers": [
                    {"firstName": "Ada", "lastName": "One", "playerId": "S76561198000000001"},
                    {"firstName": "Ben", "lastName": "Two", "playerId": "S76561198000000002"},
                ]}, "timing": {"lastLap": 90000},
            }]},
            "laps": [{"carId": 0, "driverIndex": 1, "laptime": 90000,
                      "isValidForBest": True, "splits": [30000, 30000, 30000]}],
        }
        raw = Path(self.temp.name) / "261010_091011_FP.json"
        raw.write_text(json.dumps(payload), encoding="utf-8")
        output = self.acc_provider.correct_json_format(
            str(raw), str(Path(self.temp.name) / "converted"),
            conditions={"initial_global_wetness": 1, "weather_type": "RAIN"},
        )
        self.assertIsNotNone(output)
        data = json.loads(Path(output).read_text(encoding="utf-8"))
        self.assertEqual(data["participants"][0]["steamId"], "S76561198000000001")
        self.assertEqual(data["drivers"][1]["playerId"], "S76561198000000002")
        self.assertEqual(data["laps"][0]["steamId"], "S76561198000000002")
        self.assertTrue(data["isWetSession"])
        self.assertEqual(data["conditions"]["weather_type"], "RAIN")


if __name__ == "__main__":
    unittest.main()
