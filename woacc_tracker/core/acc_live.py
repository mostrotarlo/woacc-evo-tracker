import copy
import json
import re
from datetime import datetime
from pathlib import Path
from time import monotonic

from .acc_parser import ACC_CARS
from .utils import json_file_encoding


CONNECT = re.compile(r"New connection request: id (\d+) (.+?) (S\d+) on car model (\d+)")
CAR = re.compile(r"Creating new car connection: carId (\d+), carModel (\d+)")
DISCONNECT = re.compile(r"Removing dead connection (\d+)\b")
LAP = re.compile(r"New laptime: (\d+) for carId (\d+) with lapstates:.*?\(raw (\d+)\)")
SPLITS = re.compile(r"Lap\s+carId (\d+),.*?S1 (\d+):(\d+):(\d+).*?S2 (\d+):(\d+):(\d+).*?S3 (\d+):(\d+):(\d+)")
SESSION = re.compile(r"Session changed:.*?->\s*(Practice|Qualifying|Race)\b", re.IGNORECASE)
_CACHE = {}


def _json(path: Path):
    try:
        with path.open("r", encoding=json_file_encoding(path)) as stream:
            return json.load(stream)
    except (OSError, ValueError):
        return {}


def _tail(path: Path, limit: int) -> list[str]:
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - limit))
        data = stream.read()
    if path.stat().st_size > limit:
        data = data.split(b"\n", 1)[-1]
    return data.decode("utf-8", errors="replace").splitlines()


def _cached(key: str):
    item = _CACHE.get(key)
    if item and monotonic() - item[0] < 5:
        return copy.deepcopy(item[1])
    return None


def _set_cache(key: str, value: dict):
    _CACHE[key] = (monotonic(), copy.deepcopy(value))
    return value


def _split_ms(parts) -> int:
    minutes, seconds, millis = map(int, parts)
    return minutes * 60000 + seconds * 1000 + millis


def read_acc_status(source: dict, include_details: bool = True) -> dict:
    path = Path(source.get("server_log_path") or "")
    status = {"source_name": source.get("name") or "", "server_name": source.get("name") or "",
              "log_path": str(path), "has_log": path.is_file(), "is_online": False,
              "last_log_at": "", "players_online": 0, "session_type": "", "track_name": "",
              "ambient_temperature_c": None, "track_temperature_c": None,
              "initial_global_wetness": None, "weather_type": ""}
    if not path.is_file():
        return status
    key = f"acc-status:{path}:{include_details}:{path.stat().st_size}:{path.stat().st_mtime_ns}"
    cached = _cached(key)
    if cached is not None:
        return cached
    age = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).total_seconds()
    status["is_online"] = 0 <= age <= 180
    status["last_log_at"] = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    if include_details:
        server_dir = path.parent.parent
        event = _json(server_dir / "event.json")
        settings = _json(server_dir / "settings.json")
        status["server_name"] = settings.get("serverName") or status["server_name"]
        status["track_name"] = event.get("track") or ""
        status["ambient_temperature_c"] = event.get("ambientTemp")
        status["track_temperature_c"] = event.get("trackTemp")
        status["initial_global_wetness"] = event.get("rain")
        status["weather_type"] = "RAIN" if event.get("rain") else "DRY"
        sessions = event.get("sessions") or []
        status["session_type"] = {"FP": "Practice", "P": "Practice", "Q": "Qualify", "R": "Race"}.get(
            str(sessions[0].get("sessionType") if sessions else "").upper(), "")
    lines = _tail(path, 128 * 1024 if include_details else 64 * 1024)
    count = 0
    for line in lines:
        match = SESSION.search(line)
        if match:
            status["session_type"] = "Qualify" if match.group(1).lower() == "qualifying" else match.group(1).title()
        match = re.search(r"Alive connections:\s*(\d+)", line)
        if match:
            count = int(match.group(1))
        elif CONNECT.search(line):
            count += 1
        elif DISCONNECT.search(line):
            count = max(0, count - 1)
    status["players_online"] = count
    if not status["is_online"]:
        status["players_online"] = 0
    return _set_cache(key, status)


def read_acc_leaderboard(source: dict) -> dict:
    status = read_acc_status(source)
    result = {"status": status, "entries": [], "race_pending": status.get("session_type", "").lower() == "race",
              "is_provisional": True}
    path = Path(source.get("server_log_path") or "")
    if not status["is_online"] or not path.is_file():
        return result
    key = f"acc-leaderboard:{path}:{path.stat().st_size}:{path.stat().st_mtime_ns}"
    cached = _cached(key)
    if cached is not None:
        return cached
    lines = _tail(path, 8 * 1024 * 1024)
    starts = [idx for idx, line in enumerate(lines) if SESSION.search(line)]
    if not starts:
        return result
    connections = {}
    cars = {}
    pending = None
    last_splits = {}
    laps_by_car = {}
    for line in lines:
        if SESSION.search(line):
            laps_by_car.clear()
            last_splits.clear()
            pending = None
            continue
        if re.search(r"Alive connections:\s*0\b", line):
            connections.clear()
            continue
        match = CONNECT.search(line)
        if match:
            pending = (match.group(1), match.group(2).strip(), match.group(3), int(match.group(4)))
            connections[pending[0]] = None
            continue
        match = CAR.search(line)
        if match and pending:
            cars[match.group(1)] = {"connection_id": pending[0], "driver": pending[1],
                                    "car": ACC_CARS.get(int(match.group(2)), f"ACC car #{match.group(2)}")}
            connections[pending[0]] = match.group(1)
            pending = None
            continue
        match = DISCONNECT.search(line)
        if match:
            connections.pop(match.group(1), None)
            continue
        match = SPLITS.search(line)
        if match:
            last_splits[match.group(1)] = [_split_ms(match.groups()[1:4]), _split_ms(match.groups()[4:7]), _split_ms(match.groups()[7:10])]
            continue
        match = LAP.search(line)
        if match:
            car_id = match.group(2)
            splits = last_splits.get(car_id) or [None, None, None]
            laps = laps_by_car.setdefault(car_id, [])
            laps.append({"lap_number": len(laps) + 1, "lap_time_ms": int(match.group(1)),
                         "is_valid": match.group(3) == "0", "validity": "candidate" if match.group(3) == "0" else "invalid_known",
                         "reason": "" if match.group(3) == "0" else "lapstates", "s1_ms": splits[0],
                         "s2_ms": splits[1], "s3_ms": splits[2]})

    online_cars = {car_id for car_id in connections.values() if car_id}
    status["players_online"] = len(online_cars)
    if not online_cars:
        return _set_cache(key, result)
    if result["race_pending"]:
        return _set_cache(key, result)
    for car_id, laps in laps_by_car.items():
        driver = cars.get(car_id)
        if not driver:
            continue
        valid = [lap["lap_time_ms"] for lap in laps if lap["is_valid"]]
        last = laps[-1]
        online = car_id in online_cars
        result["entries"].append({"car_id": car_id, "driver": driver["driver"], "car": driver["car"],
                                  "is_online": online, "online_state": "online" if online else "offline",
                                  "laps_total": len(laps), "laps_candidate": len(valid), "best_lap_ms": min(valid) if valid else None,
                                  "last_lap_ms": last["lap_time_ms"], "last_s1_ms": last["s1_ms"],
                                  "last_s2_ms": last["s2_ms"], "last_s3_ms": last["s3_ms"], "laps": laps})
    entries = result["entries"]
    entries.sort(key=lambda item: (item["best_lap_ms"] is None, item["best_lap_ms"] or 10**12, item["driver"]))
    leader = entries[0]["best_lap_ms"] if entries else None
    for index, entry in enumerate(entries, 1):
        entry["position"] = index
        entry["gap_ms"] = entry["best_lap_ms"] - leader if entry["best_lap_ms"] and leader else None
    return _set_cache(key, result)
