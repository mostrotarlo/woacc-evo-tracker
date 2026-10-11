import os
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import chardet
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------
# Utilities ACC
# -------------------------

def normalize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>]', "_", name).strip().replace("|", "-")

def get_domain_folder(results_dir: str, base_url: str) -> str:
    domain = base_url.replace("https://", "").replace("http://", "").strip("/")
    return os.path.join(results_dir, normalize_filename(domain))

def sha256_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()

def ms_to_laptime(ms):
    # robusto: accetta int/float, filtra valori assurdi
    try:
        if ms is None:
            return "N/A"
        if isinstance(ms, bool):
            return "N/A"
        if isinstance(ms, float):
            ms = int(ms)
        if not isinstance(ms, int) or ms <= 0:
            return "N/A"
        # >24h? probabilmente dato sporco
        if ms > 24 * 60 * 60 * 1000:
            return "N/A"
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        millis = ms % 1000
        return f"{minutes:02}:{seconds:02}:{millis:03}"
    except Exception:
        return "N/A"

CAR_ID_MAP = {
    0: "Porsche 991 GT3 R",
    1: "Mercedes-AMG GT3",
    2: "Ferrari 488 GT3",
    3: "Audi R8 LMS",
    4: "Lamborghini Huracan GT3",
    5: "McLaren 650S GT3",
    6: "Nissan GT-R Nismo GT3 2018",
    7: "BMW M6 GT3",
    8: "Bentley Continental GT3 2018",
    9: "Porsche 991II GT3 Cup",
    10: "Nissan GT-R Nismo GT3 2017",
    11: "Bentley Continental GT3 2016",
    12: "Aston Martin V12 Vantage GT23",
    13: "Lamborghini Gallardo R-EX",
    14: "Jaguar G3",
    15: "Lexus RC F GT3",
    16: "Lamborghini Huracan Evo (2019)",
    17: "Honda NSX GT3",
    18: "Lamborghini Huracan SuperTrofeo",
    19: "Audi R8 LMS Evo (2019)",
    20: "AMR V8 Vantage (2019)",
    21: "Honda NSX Evo (2019)",
    22: "McLaren 720S GT3 (2019)",
    23: "Porsche 911II GT3 R (2019)",
    24: "Ferrari 488 GT3 Evo 2020",
    25: "Mercedes-AMG GT3 2020",
    26: "Ferrari 488 Challenge Evo",
    27: "BMW M2 CS Racing",
    28: "Porsche 911 GT3 Cup (Type 992)",
    29: "Lamborghini Huracán Super Trofeo EVO2",
    30: "BMW M4 GT3 2022",
    31: "Audi R8 LMS GT3 evo II",
    32: "Ferrari 296 GT3 2023",
    33: "Lamborghini Huracan Evo2",
    34: "Porsche 992 GT3 R",
    35: "McLaren 720S GT3 Evo 2023",
    36: "Ford Mustang GT3",
    50: "Alpine A110 GT4",
    51: "AMR V8 Vantage GT4",
    52: "Audi R8 LMS GT4",
    53: "BMW M4 GT4",
    55: "Chevrolet Camaro GT4",
    56: "Ginetta G55 GT4",
    57: "KTM X-Bow GT4",
    58: "Maserati MC GT4",
    59: "McLaren 570S GT4",
    60: "Mercedes-AMG GT4",
    61: "Porsche 718 Cayman GT4",
    80: "Audi R8 LMS GT2",
    82: "KTM XBOW GT2",
    83: "Maserati MC20 GT2",
    84: "Mercedes AMG GT2",
    85: "Porsche 911 GT2 RS CS Evo",
    86: "Porsche 935"
}

def get_car_model_name(car_model_id: int) -> str:
    return CAR_ID_MAP.get(car_model_id, f"Unknown (ID {car_model_id})")

def get_driver_info(entry: dict) -> dict:
    d = (entry.get("car", {}).get("drivers") or [{}])[0]
    player_id = str(d.get("playerId") or "").strip() or None
    return {
        "driverName": f"{d.get('firstName', '')} {d.get('lastName', '')}".strip(),
        "steamId": player_id,
        "playerId": player_id,
        "carModel": get_car_model_name(entry.get("car", {}).get("carModel", -1)),
        "carNumber": entry.get("car", {}).get("raceNumber", "")
    }

def normalize_server_name(server_name: str) -> str:
    # Normalizzazione BT PADDOCK + rimozione Copy ripetuti
    parts = [p.strip() for p in (server_name or "").split(" - ")]
    clean_parts = []
    for p in parts:
        p = re.sub(r"\s+Copy(\s+Copy)*$", "", p).strip()
        if p and p not in clean_parts:
            clean_parts.append(p)
    return " - ".join(clean_parts) if clean_parts else (server_name or "Unknown")

def extract_date_time(data: dict, raw_filepath: str):
    date_field = data.get("Date", "") or data.get("date", "")
    if isinstance(date_field, str) and "T" in date_field:
        session_date = date_field.split("T")[0]
        session_time = date_field.split("T")[1].replace("Z", "")
        return session_date, session_time
    # fallback da filename: YYMMDD_HHMMSS*
    base_filename = os.path.basename(raw_filepath)
    m = re.match(r"(\d{6})_(\d{6})", base_filename)
    if m:
        yymmdd, hhmmss = m.group(1), m.group(2)
        session_date = f"20{yymmdd[:2]}-{yymmdd[2:4]}-{yymmdd[4:]}" 
        session_time = f"{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:]}" 
        return session_date, session_time
    return "0000-00-00", "00:00:00"

def correct_json_format(raw_path: str, acc_output_dir: str, conditions: Optional[dict] = None) -> Optional[str]:
    """Converte JSON raw ACC Tracker in json normalizzato.
    Ritorna il path del file output creato, oppure None se fallisce.
    """
    try:
        raw_data = Path(raw_path).read_bytes()
        encoding = chardet.detect(raw_data).get('encoding') or 'utf-8'
        content = raw_data.decode(encoding, errors="replace").lstrip('\ufeff')

        data = json.loads(content)
        session_type = data.get("sessionType", "Unknown")
        server_name = normalize_server_name(data.get("serverName", "Unknown"))
        track_name = data.get("trackName", "Unknown")
        session_date, session_time = extract_date_time(data, raw_path)

        output = {
            "trackName": track_name,
            "sessionType": session_type,
            "sessionDate": session_date,
            "sessionTime": session_time,
            "serverName": server_name
        }
        wet = data.get("sessionResult", {}).get("isWetSession")
        if wet is not None:
            output["isWetSession"] = bool(wet)
        if conditions and any(value is not None and value != "" for value in conditions.values()):
            output["conditions"] = conditions
            output["__conditions_source"] = "tracker_api"

        leaderboard = data.get("sessionResult", {}).get("leaderBoardLines", [])
        laps = data.get("laps", [])

        # Resolve co-drivers by driverIndex rather than assigning every lap to driver zero.
        car_id_to_driver = {}
        for entry in leaderboard:
            car_id = entry.get("car", {}).get("carId")
            if car_id is None:
                car_id = entry.get("carId")
            if car_id is not None:
                for index, driver in enumerate(entry.get("car", {}).get("drivers") or []):
                    player_id = str(driver.get("playerId") or "").strip() or None
                    car_id_to_driver[(str(car_id), index)] = {
                        "driverName": f"{driver.get('firstName', '')} {driver.get('lastName', '')}".strip(),
                        "steamId": player_id,
                        "playerId": player_id,
                    }
        output["drivers"] = list(car_id_to_driver.values())

        def lap_driver(lap):
            car_id = str(lap.get("carId"))
            index = int(lap.get("driverIndex") or 0)
            return car_id_to_driver.get((car_id, index), car_id_to_driver.get((car_id, 0), {
                "driverName": "Unknown", "steamId": None, "playerId": None,
            }))

        if session_type == "FP":
            output["participants"] = []
            for entry in leaderboard:
                info = get_driver_info(entry)
                last_lap = entry.get("timing", {}).get("lastLap")
                info["lastLap"] = ms_to_laptime(last_lap)
                output["participants"].append(info)

            output["laps"] = []
            lap_counters = {}
            for lap in laps:
                driver = lap_driver(lap)
                driver_name = driver["driverName"]
                lap_counters.setdefault(driver_name, 0)
                lap_counters[driver_name] += 1
                output["laps"].append({
                    "lapNumber": str(lap_counters[driver_name]),
                    "driver": driver_name,
                    "steamId": driver["steamId"],
                    "playerId": driver["playerId"],
                    "lastTime": ms_to_laptime(lap.get("laptime", -1)),
                    "isValidForBest": "Yes" if lap.get("isValidForBest") else "No",
                    "splits": [ms_to_laptime(s) for s in lap.get("splits", [])]
                })

        elif session_type == "Q":
            output["qualifyingResults"] = []
            output["laps"] = []
            for entry in leaderboard:
                info = get_driver_info(entry)
                timing = entry.get("timing", {})
                info["bestLap"] = ms_to_laptime(timing.get("bestLap"))
                info["gap"] = "N/A"
                output["qualifyingResults"].append(info)
            for idx, lap in enumerate(laps, start=1):
                driver = lap_driver(lap)
                driver_name = driver["driverName"]
                output["laps"].append({
                    "lapNumber": str(idx),
                    "driver": driver_name,
                    "steamId": driver["steamId"],
                    "playerId": driver["playerId"],
                    "lastTime": ms_to_laptime(lap.get("laptime", -1)),
                    "isValidForBest": "Yes" if lap.get("isValidForBest") else "No",
                    "splits": [ms_to_laptime(s) for s in lap.get("splits", [])]
                })

        elif session_type == "R":
            output["raceResults"] = []
            output["laps"] = []
            for entry in leaderboard:
                info = get_driver_info(entry)
                timing = entry.get("timing", {})
                info["bestLap"] = ms_to_laptime(timing.get("bestLap"))
                info["gap"] = "N/A"
                info["gapToPrevious"] = "N/A"
                info["totalTime"] = ms_to_laptime(timing.get("totalTime"))
                info["lastLap"] = ms_to_laptime(timing.get("lastLap"))
                output["raceResults"].append(info)
            for lap in laps:
                driver = lap_driver(lap)
                driver_name = driver["driverName"]
                output["laps"].append({
                    "lapNumber": str(lap.get("lapNumber", "")),
                    "driver": driver_name,
                    "steamId": driver["steamId"],
                    "playerId": driver["playerId"],
                    "lastTime": ms_to_laptime(lap.get("laptime", -1)),
                    "isValidForBest": "Yes" if lap.get("isValidForBest") else "No",
                    "splits": [ms_to_laptime(s) for s in lap.get("splits", [])]
                })

        # Salvataggio output
        Path(acc_output_dir).mkdir(parents=True, exist_ok=True)

        server_part = normalize_filename(server_name).replace("_", " ")
        date_part = session_date
        time_part = session_time.replace(":", "-")
        track_part = normalize_filename(track_name).lower()

        filename = f"{server_part}_{date_part}_{time_part}_{track_part}.json"
        new_path = str(Path(acc_output_dir) / filename)

        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return new_path
    except Exception:
        return None

# -------------------------
# Provider: scarico + conversione
# -------------------------

class AccTrackerMonitor:
    def __init__(
        self,
        *,
        base_url: str,
        results_dir: str,
        acc_output_dir: str,
        state_store,
        logger,
        verify_ssl: bool,
        user_agent: str,
        stop_event,
        batch_size: int,
        check_interval_sec: int,
        sleep_between_downloads_sec: int,
        sleep_between_batches_sec: int,
        process_all_pages: bool = False,   # ✅ NEW (default: solo prima pagina)
    ):
        self.base_url = base_url
        self.results_dir = results_dir
        self.acc_output_dir = acc_output_dir
        self.state = state_store
        self.log = logger
        self.verify_ssl = verify_ssl
        self.headers = {"User-Agent": user_agent}
        self.stop_event = stop_event
        self.batch_size = batch_size
        self.check_interval_sec = check_interval_sec
        self.sleep_between_downloads_sec = sleep_between_downloads_sec
        self.sleep_between_batches_sec = sleep_between_batches_sec

        self.process_all_pages = bool(process_all_pages)  # ✅ NEW

    def run_forever(self):
        while not self.stop_event.is_set():
            self.tick_once()
            # sleep principale
            for _ in range(int(self.check_interval_sec)):
                if self.stop_event.is_set():
                    return
                time.sleep(1)

    def tick_once(self):
        self.log.info(f"[ACC] 🔍 Controllo nuovi JSON da {self.base_url} ...")
        try:
            links = []

            if not self.process_all_pages:
                # ✅ SOLO prima pagina (default SAFE)
                response = requests.get(self.base_url, headers=self.headers, verify=self.verify_ssl, timeout=30)
                soup = BeautifulSoup(response.text, "html.parser")

                for a in soup.find_all("a", href=True):
                    full_url = urljoin(self.base_url, a["href"])
                    if full_url.lower().endswith(".json"):
                        links.append(full_url)

            else:
                # 🔥 Crawl completo paginazione
                page = 1
                while True:
                    page_url = f"{self.base_url}?page={page}"
                    response = requests.get(page_url, headers=self.headers, verify=self.verify_ssl, timeout=30)

                    if response.status_code != 200:
                        break

                    soup = BeautifulSoup(response.text, "html.parser")
                    page_links = []

                    for a in soup.find_all("a", href=True):
                        full_url = urljoin(self.base_url, a["href"])
                        if full_url.lower().endswith(".json"):
                            page_links.append(full_url)

                    if not page_links:
                        break

                    links.extend(page_links)
                    page += 1
                    time.sleep(0.5)  # protezione rate limit

            # dedup lista e filtra già visti per URL
            uniq = list(dict.fromkeys(links))
            new_links = [u for u in uniq if not self.state.url_seen(u)]

            if not new_links:
                self.log.info("[ACC] Nessun nuovo file.")
                return

            folder = get_domain_folder(self.results_dir, self.base_url)
            raw_dir = Path(folder) / "raw"
            dup_dir = Path(folder) / "duplicates"
            failed_dir = Path(folder) / "failed"
            raw_dir.mkdir(parents=True, exist_ok=True)
            dup_dir.mkdir(parents=True, exist_ok=True)
            failed_dir.mkdir(parents=True, exist_ok=True)

            # processa a batch
            for i in range(0, len(new_links), self.batch_size):
                batch = new_links[i:i + self.batch_size]
                batch_files = []

                for link in batch:
                    if self.stop_event.is_set():
                        return

                    filename = link.split("/")[-1]
                    filepath = raw_dir / filename

                    try:
                        file_resp = requests.get(link, headers=self.headers, verify=self.verify_ssl, timeout=60)
                        # protezione base
                        if "too many requests" in file_resp.text.lower():
                            raise RuntimeError("Too Many Requests")

                        content = file_resp.content
                        h = sha256_bytes(content)

                        now = time.strftime("%Y-%m-%dT%H:%M:%S")
                        self.state.mark_url(link, status="downloaded", last_seen=now, content_hash=h)

                        if self.state.hash_seen(h):
                            # duplicato già processato: salva raw in duplicates e stop
                            (dup_dir / filename).write_bytes(content)
                            self.state.mark_url(link, status="duplicate", last_seen=now, content_hash=h)
                            self.log.info(f"[ACC] ↩️ Duplicato (hash già visto): {filename}")
                            continue

                        filepath.write_bytes(content)
                        self.log.info(f"[ACC] ✅ Scaricato: {filename}")
                        batch_files.append(str(filepath))

                    except Exception as e:
                        self.log.error(f"[ACC] ❌ Errore download {filename}: {e}")
                        try:
                            self.state.mark_url(link, status="download_failed", last_seen=time.strftime("%Y-%m-%dT%H:%M:%S"))
                        except Exception:
                            pass

                    time.sleep(self.sleep_between_downloads_sec)

                # conversione batch
                for raw_path in batch_files:
                    if self.stop_event.is_set():
                        return
                    try:
                        out_path = correct_json_format(raw_path, self.acc_output_dir)
                        if out_path:
                            # marca hash ok
                            raw_bytes = Path(raw_path).read_bytes()
                            h = sha256_bytes(raw_bytes)
                            self.state.mark_hash(h, status="ok", first_seen=time.strftime("%Y-%m-%dT%H:%M:%S"), output_file=out_path)
                            # cleanup: elimina raw
                            Path(raw_path).unlink(missing_ok=True)
                            self.log.info(f"[ACC] 🔁 Convertito: {Path(out_path).name}")
                        else:
                            # sposta in failed
                            p = Path(raw_path)
                            p.replace(failed_dir / p.name)
                            self.log.error(f"[ACC] ❌ Conversione fallita: {p.name}")
                    except Exception as e:
                        self.log.error(f"[ACC] ❌ Errore conversione {Path(raw_path).name}: {e}")

                # salva stato dopo batch
                try:
                    self.state.save()
                except Exception:
                    pass

                # pausa tra batch
                for _ in range(int(self.sleep_between_batches_sec)):
                    if self.stop_event.is_set():
                        return
                    time.sleep(1)

        except Exception as e:
            self.log.error(f"[ACC] ⚠️ Errore nel controllo: {e}")
