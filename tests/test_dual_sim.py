import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from woacc_tracker.core.acc_parser import parse_acc_results
from woacc_tracker.core.acc_live import read_acc_leaderboard
from woacc_tracker.core.database import Database
from woacc_tracker.core.importer import Importer
from woacc_tracker.core.source_discovery import discover_managed_sources, sync_managed_sources
from woacc_tracker.core.config import DEFAULT_WOACC_API_KEY
from woacc_tracker.web.app import create_app


class DualSimTest(unittest.TestCase):
    def test_proxy_prefix_static_links_and_direct_access(self):
        app = create_app(self.db, {"base_path": "/tracker", "tracker_mode": "both", "sources": []})
        client = app.test_client()
        headers = {"X-Forwarded-Prefix": "/tracker", "X-Forwarded-Host": "tracker.example.com", "X-Forwarded-Proto": "https"}
        page = client.get("/", headers=headers)
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'/tracker/static/style.css', page.data)
        self.assertNotIn(b'/tracker/tracker/', page.data)
        with client.get("/static/style.css", headers=headers) as asset:
            self.assertEqual(asset.status_code, 200)
        direct = client.get("/", environ_overrides={"SCRIPT_NAME": ""})
        self.assertIn(b'/static/style.css', direct.data)
        self.assertNotIn(b'/tracker/static/style.css', direct.data)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp.name)
        self.db = Database(str(self.root / "tracker.db"))
        self.db.init_schema()
        self.importer = Importer(self.db, log=lambda _message: None)

    def tearDown(self):
        self.temp.cleanup()

    def _acc_file(self):
        path = self.root / "acc_results" / "261010_120000_Q.json"
        path.parent.mkdir()
        data = {
            "serverName": "Shared name", "trackName": "monza", "sessionType": "Q",
            "sessionResult": {"isWetSession": 1, "leaderBoardLines": [
                {"car": {"carId": 1001, "carModel": 32, "raceNumber": 7, "cupCategory": 0,
                         "drivers": [{"firstName": "Ada", "lastName": "Test", "playerId": "S123"}]},
                 "currentDriver": {"firstName": "Ada", "lastName": "Test", "playerId": "S123"},
                 "timing": {"totalTime": 300000}}
            ]},
            "laps": [
                {"carId": 1001, "driverIndex": 0, "laptime": 98000, "isValidForBest": False, "splits": [30000, 35000, 33000]},
                {"carId": 1001, "driverIndex": 0, "laptime": 100000, "isValidForBest": True, "splits": [31000, 36000, 33000]},
            ],
        }
        path.write_text(json.dumps(data), encoding="utf-16")
        return path

    def _evo_file(self):
        path = self.root / "evo_result" / "results_20261010_120000_practice.json"
        path.parent.mkdir()
        data = {
            "server_name": "Shared name", "track_name": "monza", "session_type": "Practice",
            "is_completed": True,
            "drivers": [{"guid": {"a": 1, "b": 2}, "first_name": "Ben", "last_name": "Test", "player_id": "456"}],
            "cars": [{"car_id": {"a": 3, "b": 4}, "model_displayname": "Ferrari 296 GT3", "race_number": 8}],
            "laps": [{"driver_key": {"a": 1, "b": 2}, "car_key": {"a": 3, "b": 4},
                      "time": 101000, "split": [30000, 35000, 36000], "flags": 2}],
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_folder_scan_reuses_unchanged_file_metadata(self):
        path = self._evo_file()
        source = {"sim": "evo"}
        self.assertEqual(self.importer.import_folder(path.parent, "evo", source)["imported"], 1)
        with patch.object(self.importer, "import_file", return_value="skipped") as import_file:
            stats = self.importer.import_folder(path.parent, "evo", source)
            self.assertEqual(stats["skipped"], 1)
            import_file.assert_not_called()

            mtime = path.stat().st_mtime_ns + 1_000_000_000
            os.utime(path, ns=(mtime, mtime))
            self.importer.import_folder(path.parent, "evo", source)
            import_file.assert_called_once()

        self.assertIn("idx_sessions_server_id", {row[1] for row in self.db.query("PRAGMA index_list(sessions)")})
        self.assertIn("idx_session_entries_session_id", {row[1] for row in self.db.query("PRAGMA index_list(session_entries)")})

    def test_import_transaction_rolls_back_on_failure(self):
        with self.assertRaises(RuntimeError):
            with self.db.transaction():
                self.db.execute("INSERT INTO app_meta(key, value) VALUES(?, ?)", ("rollback_test", "1"))
                raise RuntimeError("failed import")
        self.assertIsNone(self.db.one("SELECT value FROM app_meta WHERE key=?", ("rollback_test",)))
        self.assertEqual(self.importer.import_folder(self._evo_file().parent, "evo", {"sim": "evo"})["imported"], 1)

    def test_acc_parser_uses_official_validity(self):
        parsed = parse_acc_results(self._acc_file())
        self.assertEqual(parsed["entries"][0]["best_lap_ms"], 100000)
        self.assertEqual(parsed["entries"][0]["laps_valid"], 1)
        self.assertEqual(parsed["entries"][0]["car_name"], "Ferrari 296 GT3")
        self.assertEqual(parsed["weather"]["weather_type"], "RAIN")
        self.assertIsNone(parsed["weather"]["initial_global_wetness"])
        self.assertEqual(parsed["entries"][0]["steam_id"], "S123")
        self.assertIsNone(parsed["weather"]["ambient_temperature_c"])
        self.assertIsNone(parsed["weather"]["track_temperature_c"])
        self.assertIsNone(parsed["weather"]["track_grip"])

    def test_acc_event_rain_setting_does_not_override_dry_session_flag(self):
        path = self._acc_file()
        data = json.loads(path.read_text(encoding="utf-16"))
        data["sessionResult"]["isWetSession"] = 0
        path.write_text(json.dumps(data), encoding="utf-16")
        event = path.parent.parent / "event.json"
        event.write_text(json.dumps({"rain": 0.022}), encoding="utf-8")

        weather = parse_acc_results(path)["weather"]
        self.assertEqual(weather["weather_type"], "DRY")
        self.assertIsNone(weather["precipitation"])
        self.assertIsNone(weather["initial_global_wetness"])

    def test_existing_acc_session_weather_is_refreshed_from_event_file(self):
        path = self._acc_file()
        data = json.loads(path.read_text(encoding="utf-16"))
        data["sessionResult"]["isWetSession"] = 0
        path.write_text(json.dumps(data), encoding="utf-16")
        source_id = self.importer.ensure_source(path.parent, "ACC", {"sim": "acc"})
        self.assertEqual(self.importer.import_file(path, source_id), "imported")
        session_id = self.db.one("SELECT id FROM sessions WHERE sim='acc'")["id"]
        self.db.execute(
            "UPDATE sessions SET weather_type='DRY', initial_global_wetness=0 WHERE id=?",
            (session_id,),
        )

        event = path.parent.parent / "event.json"
        event.write_text(json.dumps({"track": "monza", "ambientTemp": 17, "trackTemp": 27,
                                    "rain": 0.022, "weatherRandomness": 2}), encoding="utf-16")
        event_time = datetime(2026, 10, 10, 11).timestamp()
        os.utime(event, (event_time, event_time))
        original = path.read_bytes()

        self.assertEqual(self.importer.import_file(path, source_id), "skipped")
        row = self.db.one(
            "SELECT weather_type, precipitation, initial_global_wetness, ambient_temperature_c, track_temperature_c FROM sessions WHERE id=?",
            (session_id,),
        )
        self.assertEqual(row["weather_type"], "DRY")
        self.assertIsNone(row["precipitation"])
        self.assertIsNone(row["initial_global_wetness"])
        self.assertEqual(row["ambient_temperature_c"], 17)
        self.assertEqual(row["track_temperature_c"], 27)
        self.assertEqual(path.read_bytes(), original)
        cfg = {"tracker_mode": "both", "default_sim": "acc", "language": "it", "sources": [],
               "theme": {}, "woacc_api_enabled": True, "woacc_api_key": DEFAULT_WOACC_API_KEY,
               "password_enabled": False, "base_path": ""}
        client = create_app(self.db, cfg).test_client()
        conditions = client.get("/api/woacc/sessions?sim=acc",
                                headers={"X-WOACC-API-Key": DEFAULT_WOACC_API_KEY}).get_json()["items"][0]["conditions"]
        self.assertEqual(conditions["ambient_temperature_c"], 17)
        self.assertEqual(conditions["track_temperature_c"], 27)
        self.assertIn("Asciutto | Aria 17.0", client.get("/").data.decode("utf-8"))

    def test_acc_config_temperature_does_not_use_later_or_other_track_settings(self):
        path = self._acc_file()
        event = path.parent.parent / "event.json"
        event.write_text(json.dumps({"track": "monza", "ambientTemp": 24}), encoding="utf-8")
        later = datetime(2026, 10, 10, 13).timestamp()
        os.utime(event, (later, later))
        self.assertIsNone(parse_acc_results(path)["weather"]["ambient_temperature_c"])

        event.write_text(json.dumps({"track": "suzuka", "ambientTemp": 24}), encoding="utf-8")
        earlier = datetime(2026, 10, 10, 11).timestamp()
        os.utime(event, (earlier, earlier))
        self.assertIsNone(parse_acc_results(path)["weather"]["ambient_temperature_c"])

        event.write_text(json.dumps({"track": "monza", "ambientTemp": 24}), encoding="utf-8")
        os.utime(event, (earlier, earlier))
        weather = parse_acc_results(path)["weather"]
        self.assertEqual(weather["ambient_temperature_c"], 24)
        self.assertIsNone(weather["track_temperature_c"])
        self.assertIsNone(weather["track_grip"])

    def test_acc_old_session_shows_missing_values_and_default_view(self):
        path = self._acc_file()
        source_id = self.importer.ensure_source(path.parent, "ACC", {"sim": "acc"})
        self.assertEqual(self.importer.import_file(path, source_id), "imported")
        session_id = self.db.one("SELECT id FROM sessions WHERE sim='acc'")["id"]
        cfg = {"tracker_mode": "both", "default_sim": "acc", "language": "it",
               "sources": [], "theme": {}, "woacc_api_enabled": False,
               "password_enabled": False, "base_path": ""}
        client = create_app(self.db, cfg).test_client()
        self.assertIn(b"Ada Test", client.get("/leaderboard").data)
        page = client.get(f"/session/{session_id}").data.decode("utf-8")
        self.assertIn("<span>Aria</span><strong>ND</strong>", page)
        self.assertIn("<span>Pista</span><strong>ND</strong>", page)
        self.assertIn("<span>Steam ID</span><strong>S123</strong>", page)
        client.get("/select-sim/evo")
        self.assertNotIn(b"Ada Test", client.get("/leaderboard").data)
        cfg["default_sim"] = "evo"
        self.assertNotIn(b"Ada Test", client.get("/leaderboard").data)
        cfg["default_sim"] = "acc"
        self.assertIn(b"Ada Test", client.get("/leaderboard").data)

    def test_acc_explicit_conditions_are_preserved_without_changing_original(self):
        path = self._acc_file()
        data = json.loads(path.read_text(encoding="utf-16"))
        data["conditions"] = {"ambient_temperature_c": 23.4,
                              "track_temperature_c": 31.2, "track_grip": 0.98}
        path.write_text(json.dumps(data), encoding="utf-16")
        original = path.read_bytes()
        source_id = self.importer.ensure_source(path.parent, "ACC", {"sim": "acc"})
        self.assertEqual(self.importer.import_file(path, source_id), "imported")
        row = self.db.one("SELECT ambient_temperature_c, track_temperature_c, track_grip FROM sessions WHERE sim='acc'")
        self.assertEqual(tuple(row), (23.4, 31.2, 0.98))
        self.assertEqual(path.read_bytes(), original)

    def test_import_and_web_keep_simulators_separate(self):
        acc = self._acc_file()
        evo = self._evo_file()
        for path, sim in ((acc, "acc"), (evo, "evo")):
            source_id = self.importer.ensure_source(path.parent, sim, {"sim": sim})
            self.assertEqual(self.importer.import_file(path, source_id), "imported")
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM servers")["n"], 2)
        cfg = {"tracker_mode": "both", "sources": [], "theme": {}, "woacc_api_enabled": False,
               "password_enabled": False, "base_path": ""}
        app = create_app(self.db, cfg)
        client = app.test_client()
        self.assertEqual(client.get("/sessions").status_code, 200)
        self.assertIn(b"Ben Test", client.get("/leaderboard").data)
        self.assertNotIn(b"Ada Test", client.get("/leaderboard").data)
        self.assertEqual(client.get("/select-sim/acc").status_code, 302)
        self.assertIn(b"Ada Test", client.get("/leaderboard").data)
        self.assertNotIn(b"Ben Test", client.get("/leaderboard").data)
        for endpoint in ("/", "/servers", "/sessions", "/records", "/licenses"):
            self.assertEqual(client.get(endpoint).status_code, 200, endpoint)
        app_with_prefix = create_app(self.db, dict(cfg, base_path="/tracker"))
        prefixed_client = app_with_prefix.test_client()
        response = prefixed_client.get("/select-sim/acc")
        self.assertIn("Path=/", response.headers["Set-Cookie"])
        self.assertIn(b"Ada Test", prefixed_client.get("/leaderboard").data)
        bridge_app = create_app(self.db, dict(cfg, woacc_api_enabled=True, woacc_api_key=DEFAULT_WOACC_API_KEY))
        bridge = bridge_app.test_client()
        headers = {"X-WOACC-API-Key": DEFAULT_WOACC_API_KEY}
        index = bridge.get("/api/woacc/sessions", headers=headers).get_json()
        self.assertEqual(index["count"], 1)
        self.assertEqual(index["items"][0]["sim"], "evo")
        acc_session_id = self.db.one("SELECT id FROM sessions WHERE sim='acc'")["id"]
        acc_index = bridge.get("/api/woacc/sessions?sim=acc", headers=headers).get_json()
        self.assertEqual(acc_index["count"], 1)
        self.assertEqual(acc_index["items"][0]["sim"], "acc")
        self.assertEqual(bridge.get("/api/woacc/sessions?sim=all", headers=headers).get_json()["count"], 2)
        original = bridge.get(f"/api/woacc/session/{acc_session_id}/original.json", headers=headers)
        self.assertEqual(original.status_code, 200)
        self.assertEqual(original.data, acc.read_bytes())

    def test_bomless_utf16_acc_result(self):
        path = self._acc_file()
        path.write_bytes(path.read_text(encoding="utf-16").encode("utf-16-le"))
        self.assertEqual(parse_acc_results(path)["entries"][0]["laps_valid"], 1)

    def test_manager_sync_preserves_source_options(self):
        manager = self.root / "accweb"
        server = manager / "config" / "100"
        (server / "results").mkdir(parents=True)
        (server / "settings.json").write_text(json.dumps({"serverName": "My ACC"}), encoding="utf-16")
        (server / "accwebConfig.json").write_text("{}", encoding="utf-8")
        self.assertEqual(len(discover_managed_sources("acc", str(manager))), 1)
        cfg = {"sources": [], "accweb_path": str(manager), "evo_manager_path": ""}
        self.assertTrue(sync_managed_sources(cfg))
        cfg["sources"][0]["announce_records"] = True
        self.assertFalse(sync_managed_sources(cfg))
        self.assertTrue(cfg["sources"][0]["announce_records"])
        manager.rename(self.root / "temporarily_offline")
        self.assertFalse(sync_managed_sources(cfg))
        self.assertEqual(len(cfg["sources"]), 1)

    def test_existing_evo_source_is_adopted_without_losing_settings(self):
        manager = self.root / "manager"
        server = manager / "servers" / "server_1"
        server.mkdir(parents=True)
        (server / "server.json").write_text(json.dumps({"name": "Manager name"}), encoding="utf-8")
        result_path = str((server / "result").resolve())
        cfg = {"sources": [{"name": "Custom name", "path": result_path, "sim": "evo", "enabled": False,
                            "server_log_path": "custom.log", "announce_records": True}],
               "evo_manager_path": str(manager), "accweb_path": ""}
        self.assertTrue(sync_managed_sources(cfg))
        source = cfg["sources"][0]
        self.assertEqual(source["name"], "Custom name")
        self.assertEqual(source["server_log_path"], "custom.log")
        self.assertFalse(source["enabled"])
        self.assertTrue(source["announce_records"])
        self.assertEqual(source["managed_by"], "evo_manager")

    def test_unchanged_result_does_not_rehash(self):
        path = self._acc_file()
        source_id = self.importer.ensure_source(path.parent, "ACC", {"sim": "acc"})
        self.assertEqual(self.importer.import_file(path, source_id), "imported")
        with patch("woacc_tracker.core.importer.file_sha256", side_effect=AssertionError("rehash")):
            self.assertEqual(self.importer.import_file(path, source_id), "skipped")

    def test_acc_live_resets_laps_on_session_change(self):
        path = self.root / "server.log"
        path.write_text("\n".join([
            "Session changed: Qualifying -> Qualifying 0",
            "New connection request: id 1 Ada Test S123 on car model 32",
            "Creating new car connection: carId 1001, carModel 32",
            "New laptime: 100000 for carId 1001 with lapstates:  (raw 0)",
            "Session changed: Qualifying -> Qualifying 1",
            "New laptime: 99000 for carId 1001 with lapstates: HasCut,  (raw 1)",
            "New laptime: 101000 for carId 1001 with lapstates:  (raw 0)",
        ]), encoding="utf-8")
        source = {"name": "ACC", "sim": "acc", "server_log_path": str(path)}
        result = read_acc_leaderboard(source)
        self.assertEqual(result["status"]["players_online"], 1)
        self.assertEqual(result["entries"][0]["best_lap_ms"], 101000)
        self.assertEqual(result["entries"][0]["laps_candidate"], 1)


if __name__ == "__main__":
    unittest.main()
