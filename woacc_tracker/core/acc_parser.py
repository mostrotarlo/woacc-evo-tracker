import json
import math
import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from .parser import file_sha256
from .utils import json_file_encoding, make_server_key


ACC_CARS = {
    0: "Porsche 991 GT3 R", 1: "Mercedes-AMG GT3", 2: "Ferrari 488 GT3",
    3: "Audi R8 LMS", 4: "Lamborghini Huracan GT3", 5: "McLaren 650S GT3",
    6: "Nissan GT-R Nismo GT3 2018", 7: "BMW M6 GT3",
    8: "Bentley Continental GT3 2018", 9: "Porsche 991II GT3 Cup",
    10: "Nissan GT-R Nismo GT3 2017", 11: "Bentley Continental GT3 2016",
    12: "Aston Martin V12 Vantage GT3", 13: "Lamborghini Gallardo R-EX",
    14: "Jaguar G3", 15: "Lexus RC F GT3", 16: "Lamborghini Huracan Evo",
    17: "Honda NSX GT3", 18: "Lamborghini Huracan SuperTrofeo",
    19: "Audi R8 LMS Evo", 20: "Aston Martin V8 Vantage GT3",
    21: "Honda NSX Evo", 22: "McLaren 720S GT3", 23: "Porsche 991II GT3 R",
    24: "Ferrari 488 GT3 Evo", 25: "Mercedes-AMG GT3 2020",
    26: "Ferrari 488 Challenge Evo", 27: "BMW M2 CS Racing",
    28: "Porsche 992 GT3 Cup", 29: "Lamborghini Super Trofeo EVO2",
    30: "BMW M4 GT3", 31: "Audi R8 LMS GT3 Evo II", 32: "Ferrari 296 GT3",
    33: "Lamborghini Huracan GT3 Evo2", 34: "Porsche 992 GT3 R",
    35: "McLaren 720S GT3 Evo", 36: "Ford Mustang GT3",
}


def _ms(value):
    try:
        value = int(value)
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _timestamp(path: Path) -> str:
    match = re.match(r"(\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_", path.name)
    if match:
        try:
            return datetime.strptime("".join(match.groups()), "%y%m%d%H%M%S").isoformat(timespec="seconds")
        except ValueError:
            pass
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


@lru_cache(maxsize=128)
def _read_event_config(path: str, size: int, mtime_ns: int) -> dict:
    event_path = Path(path)
    with event_path.open("r", encoding=json_file_encoding(event_path)) as stream:
        event = json.load(stream)
    return event if isinstance(event, dict) else {}


def _configured_temperatures(path: Path, session_datetime: str, track_name: str) -> dict:
    event_path = path.parent.parent / "event.json"
    try:
        stat = event_path.stat()
        # A newer configuration cannot describe an archived session reliably.
        if datetime.fromtimestamp(stat.st_mtime) > datetime.fromisoformat(session_datetime):
            return {}
        event = _read_event_config(str(event_path), stat.st_size, stat.st_mtime_ns)
        if event.get("track") and str(event["track"]).strip().lower() != track_name.strip().lower():
            return {}
        return {
            "ambient_temperature_c": _number(event.get("ambientTemp")),
            "track_temperature_c": _number(event.get("trackTemp")),
        }
    except (OSError, ValueError, TypeError):
        return {}


def _driver_name(driver: dict) -> str:
    return " ".join(str(driver.get(key) or "").strip() for key in ("firstName", "lastName")).strip() or str(driver.get("shortName") or "Unknown driver")


def _acc_weather(data: dict, path: Path, session_datetime: str) -> dict:
    wet = (data.get("sessionResult") or {}).get("isWetSession")
    conditions = data.get("conditions") if isinstance(data.get("conditions"), dict) else {}
    configured = _configured_temperatures(path, session_datetime, data.get("trackName") or "Unknown track")
    temperatures = {}
    for key in ("ambient_temperature_c", "track_temperature_c"):
        value = _number(conditions.get(key))
        temperatures[key] = configured.get(key) if value is None else value
    precipitation = _number(conditions.get("precipitation"))
    wetness = _number(conditions.get("initial_global_wetness"))
    is_wet = wet is True or wet == 1 or (precipitation is not None and precipitation > 0) or (
        wetness is not None and wetness > 0
    )
    return {
        "initial_global_wetness": wetness,
        "weather_type": "RAIN" if is_wet else "DRY" if wet is not None or precipitation is not None else "",
        "precipitation": precipitation,
        **temperatures,
        "track_grip": _number(conditions.get("track_grip")),
    }


def read_acc_result_weather(path: Path) -> dict:
    with path.open("r", encoding=json_file_encoding(path)) as stream:
        data = json.load(stream)
    return _acc_weather(data, path, _timestamp(path))


def parse_acc_results(path: Path) -> dict:
    with path.open("r", encoding=json_file_encoding(path)) as stream:
        data = json.load(stream)
    if not isinstance(data.get("sessionResult"), dict) or not isinstance(data.get("laps"), list):
        raise ValueError("Not an ACC session result")

    session_result = data["sessionResult"]
    lines = session_result.get("leaderBoardLines") or []
    grouped = defaultdict(list)
    for lap in data["laps"]:
        if _ms(lap.get("laptime")):
            grouped[(str(lap.get("carId")), int(lap.get("driverIndex") or 0))].append(lap)

    entries = []
    for position, line in enumerate(lines, 1):
        car = line.get("car") or {}
        car_id = str(car.get("carId"))
        drivers = car.get("drivers") or []
        if not isinstance(drivers, list):
            drivers = []
        current = line.get("currentDriver") or {}
        if not drivers and current:
            drivers = [current]
        for driver_index, driver in enumerate(drivers):
            if not isinstance(driver, dict):
                continue
            laps = grouped.pop((car_id, driver_index), [])
            parsed_laps = []
            valid_times = []
            all_times = []
            valid_splits = [[], [], []]
            for number, lap in enumerate(laps, 1):
                time_ms = _ms(lap.get("laptime"))
                valid = lap.get("isValidForBest") is True
                splits = [(_ms(value) if value is not None else None) for value in (lap.get("splits") or [])[:3]]
                splits.extend([None] * (3 - len(splits)))
                all_times.append(time_ms)
                if valid:
                    valid_times.append(time_ms)
                    for idx, split in enumerate(splits):
                        if split:
                            valid_splits[idx].append(split)
                parsed_laps.append({"lap_number": number, "lap_time_ms": time_ms, "is_valid": valid,
                                    "invalid_reason": "" if valid else "acc_invalid", "flags": None,
                                    "s1_ms": splits[0], "s2_ms": splits[1], "s3_ms": splits[2]})
            model = car.get("carModel")
            category = {0: "PRO", 1: "PRO-AM", 2: "AM", 3: "SILVER"}.get(car.get("cupCategory"), "")
            player_id = str(driver.get("playerId") or "").strip()
            entries.append({
                "driver_key": player_id or f"acc:{car_id}:{driver_index}:{_driver_name(driver)}",
                "steam_id": player_id or None,
                "display_name": _driver_name(driver), "nation": "", "driver_category": category,
                "car_key": car_id, "car_name": ACC_CARS.get(model, f"ACC car #{model}"),
                "race_number": car.get("raceNumber"), "position": position,
                "best_lap_ms": min(valid_times) if valid_times else None,
                "potential_lap_ms": sum(min(v) for v in valid_splits) if all(valid_splits) else None,
                "avg_valid_lap_ms": round(sum(valid_times) / len(valid_times)) if valid_times else None,
                "avg_all_lap_ms": round(sum(all_times) / len(all_times)) if all_times else None,
                "laps_total": len(parsed_laps), "laps_valid": len(valid_times), "laps": parsed_laps,
                "race_total_time_ms": _ms((line.get("timing") or {}).get("totalTime")),
                "status": "Finished" if parsed_laps else "No laps",
            })

    session_type = {"FP": "Practice", "P": "Practice", "Q": "Qualify", "R": "Race"}.get(str(data.get("sessionType") or "").upper(), "Unknown")
    if session_type != "Race":
        entries.sort(key=lambda entry: (entry["best_lap_ms"] is None, entry["best_lap_ms"] or 10**12, entry["display_name"]))
        for position, entry in enumerate(entries, 1):
            entry["position"] = position
            entry["gap_ms"] = entry["best_lap_ms"] - entries[0]["best_lap_ms"] if entry["best_lap_ms"] and entries[0]["best_lap_ms"] else None
    else:
        leader_time = entries[0]["race_total_time_ms"] if entries else None
        leader_laps = entries[0]["laps_total"] if entries else None
        for entry in entries:
            same_lap = entry["laps_total"] == leader_laps
            entry["gap_ms"] = entry["race_total_time_ms"] - leader_time if same_lap and entry["race_total_time_ms"] and leader_time and entry["position"] > 1 else None

    server_name = data.get("serverName") or "ACC server"
    track_name = data.get("trackName") or "Unknown track"
    session_datetime = _timestamp(path)
    return {
        "sim": "acc", "file_hash": file_sha256(path), "file_path": str(path),
        "server_name": server_name, "track_name": track_name, "track_layout": "",
        "server_key": "acc::" + make_server_key(server_name, track_name),
        "session_name": "", "session_type": session_type, "session_datetime": session_datetime,
        "is_completed": True, "laps_total": sum(entry["laps_total"] for entry in entries),
        "drivers_count": len(entries), "best_lap_ms": min((entry["best_lap_ms"] for entry in entries if entry["best_lap_ms"]), default=None),
        "weather": _acc_weather(data, path, session_datetime),
        "entries": entries,
    }
