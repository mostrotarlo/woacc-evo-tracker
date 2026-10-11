import json
import time
import hashlib
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from providers.evo_converter2 import convert_evo_json, save_converted_json
from providers.acc_provider import correct_json_format


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def normalize_tracker_base_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""

    # 👉 gestione http/https intelligente
    if not url.startswith(("http://", "https://")):
        if ":" in url:  # IP con porta → probabilmente http
            url = "http://" + url
        else:
            url = "https://" + url

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # pagine UI → torniamo alla root tracker
    known_pages = ("/leaderboard", "/sessions", "/servers", "/records", "/logs", "/login")
    for suffix in known_pages:
        if path.endswith(suffix):
            path = path[: -len(suffix)].rstrip("/")
            break

    # se già API → risaliamo alla base
    marker = "/api/woacc"
    if marker in path:
        path = path.split(marker, 1)[0].rstrip("/")

    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", "")).rstrip("/")


def tracker_api_url(base_url: str, endpoint: str) -> str:
    base_url = normalize_tracker_base_url(base_url)
    return base_url.rstrip("/") + endpoint

from urllib.parse import urlparse

def build_download_url(base_url: str, download_url: str) -> str:
    base_url = normalize_tracker_base_url(base_url)
    download_url = (download_url or "").strip()

    # URL già completo
    if download_url.startswith(("http://", "https://")):
        return download_url

    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    base_path = parsed.path.rstrip("/")

    # Caso: /tracker/api/...
    if base_path and download_url.startswith(base_path + "/"):
        return origin + download_url

    # Caso: /api/...
    if download_url.startswith("/api/"):
        return base_url.rstrip("/") + download_url

    # Caso: api/...
    if download_url.startswith("api/"):
        return base_url.rstrip("/") + "/" + download_url

    # fallback generico
    return base_url.rstrip("/") + "/" + download_url.lstrip("/")


def safe_filename(name: str) -> str:
    bad = '\\/*?:"<>|'
    for ch in bad:
        name = name.replace(ch, "_")
    return name.strip() or "evo_session.json"


class EvoTrackerMonitor:
    def __init__(
        self,
        *,
        base_url: str,
        results_dir: str,
        session_json_dir: str,
        state_store,
        logger,
        verify_ssl: bool,
        user_agent: str,
        stop_event,
        batch_size: int,
        check_interval_sec: int,
        sleep_between_downloads_sec: int,
        api_key: str = "",
        api_limit: int = 1000,
        acc_output_dir: str | None = None,
        acc_backfill_existing: bool = False,
    ):
        self.base_url = normalize_tracker_base_url(base_url)
        self.results_dir = Path(results_dir)
        self.session_json_dir = Path(session_json_dir)
        self.acc_output_dir = Path(acc_output_dir) if acc_output_dir else self.session_json_dir
        self.state = state_store
        self.log = logger
        self.verify_ssl = verify_ssl
        self.headers = {"User-Agent": user_agent}
        if api_key:
            self.headers["X-WOACC-API-Key"] = api_key
        self.stop_event = stop_event
        self.batch_size = int(batch_size)
        self.check_interval_sec = int(check_interval_sec)
        self.sleep_between_downloads_sec = int(sleep_between_downloads_sec)
        self.api_limit = int(api_limit)
        self.acc_backfill_existing = bool(acc_backfill_existing)
        self.started_at = datetime.now().astimezone()

    @staticmethod
    def _state_key(item: dict) -> str:
        file_hash = str(item.get("file_hash") or "").strip()
        return ("sha256:" if item["sim"] == "acc" else "evo:") + file_hash

    def _baseline_existing_acc(self, entries: list[dict]) -> None:
        marker = "acc-api-baseline:" + hashlib.sha1(self.base_url.encode("utf-8")).hexdigest()
        if self.acc_backfill_existing:
            return
        saved = getattr(self.state, "data", {}).get("processed_hashes", {}).get(marker, {})
        try:
            cutoff = datetime.fromisoformat(saved.get("first_seen") or "")
        except ValueError:
            cutoff = self.started_at
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=self.started_at.tzinfo)
        baseline_count = 0
        for item in entries:
            file_hash = str(item.get("file_hash") or "").strip()
            if not file_hash:
                continue
            try:
                session_at = datetime.fromisoformat(str(item.get("session_datetime") or item.get("imported_at") or ""))
                if session_at.tzinfo is None:
                    session_at = session_at.replace(tzinfo=self.started_at.tzinfo)
                if session_at > cutoff:
                    continue
            except ValueError:
                pass
            state_key = self._state_key(item)
            if not self.state.hash_seen(state_key):
                self.state.mark_hash(state_key, status="baseline", first_seen=now_iso(), output_file="")
                baseline_count += 1
        if not self.state.hash_seen(marker):
            self.state.mark_hash(marker, status="baseline", first_seen=cutoff.isoformat(timespec="seconds"), output_file="")
        if baseline_count or not saved:
            self.state.save()
        if baseline_count:
            self.log.info(f"[ACC] {baseline_count} sessioni precedenti al punto iniziale escluse.")

    def run_forever(self):
        while not self.stop_event.is_set():
            self.tick_once()
            for _ in range(max(1, self.check_interval_sec)):
                if self.stop_event.is_set():
                    return
                time.sleep(1)

    def _api_get_json(self, url: str, timeout: int = 45):
        r = requests.get(url, headers=self.headers, verify=self.verify_ssl, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def _download_bytes(self, url: str) -> bytes:
        r = requests.get(url, headers=self.headers, verify=self.verify_ssl, timeout=90)
        r.raise_for_status()
        return r.content

    def _raw_dir(self, sim: str) -> Path:
        parsed = urlparse(self.base_url)
        folder = (parsed.netloc + parsed.path).strip("/").replace("/", "_").replace(":", "_")
        p = self.results_dir / f"{sim.upper()}_{safe_filename(folder)}" / "raw"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def _acc_raw_name(item: dict, file_hash: str) -> str:
        try:
            stamp = datetime.fromisoformat(str(item.get("session_datetime") or ""))
            prefix = stamp.strftime("%y%m%d_%H%M%S")
        except ValueError:
            prefix = Path(str(item.get("file_path") or "")).name[:13]
        if len(prefix) != 13 or prefix[6] != "_" or not prefix.replace("_", "").isdigit():
            raise ValueError("ACC session has no usable timestamp")
        return f"{prefix}_tracker_{item['session_id']}_{file_hash[:12]}.json"

    def tick_once(self):
        if not self.base_url:
            self.log.error("[EVO] URL tracker vuoto.")
            return

        try:
            ping_url = tracker_api_url(self.base_url, "/api/woacc/ping")
            self.log.info(f"[WOACC] Controllo API Tracker: {self.base_url}")

            supported_sims = []
            try:
                ping = self._api_get_json(ping_url, timeout=20)
                if not ping.get("ok"):
                    self.log.warning(f"[WOACC] Ping API non OK: {ping}")
                supported_sims = ping.get("supported_sims", []) or []
            except Exception as e:
                self.log.warning(f"[WOACC] Ping API non riuscito, provo comunque sessions: {e}")

            sims = ("evo", "acc") if "acc" in supported_sims else ("evo",)
            by_sim = []
            for sim in sims:
                sessions_url = tracker_api_url(
                    self.base_url,
                    f"/api/woacc/sessions?status=imported&limit={self.api_limit}&sim={sim}",
                )
                data = self._api_get_json(sessions_url, timeout=45)
                entries = data.get("items", []) if isinstance(data, dict) else []
                filtered = [
                    dict(item, sim=sim)
                    for item in reversed(entries)
                    if isinstance(item, dict) and (item.get("sim") or "evo").lower() == sim
                ]
                if sim == "acc":
                    self._baseline_existing_acc(filtered)
                by_sim.append(filtered)

            # Alternate simulators so a large EVO backlog does not delay ACC imports.
            items = [item for row in zip_longest(*by_sim) for item in row if item]
            if not items:
                self.log.info("[WOACC] Nessuna sessione disponibile dall'API WOACC.")
                return

            new_items = []
            for item in items:
                file_hash = (item.get("file_hash") or "").strip()
                session_id = item.get("session_id")
                download_url = item.get("download_url")
                if not file_hash or not session_id or not download_url:
                    continue
                state_key = self._state_key(item)
                if self.state.hash_seen(state_key):
                    continue
                new_items.append(item)

            if not new_items:
                self.log.info("[WOACC] Nessun nuovo JSON da importare.")
                return

            self.session_json_dir.mkdir(parents=True, exist_ok=True)
            self.log.info(f"[WOACC] Trovati {len(new_items)} nuovi JSON.")

            converted_count = 0
            skipped_count = 0
            failed_count = 0

            for idx, item in enumerate(new_items[: self.batch_size], start=1):
                if self.stop_event.is_set():
                    return

                file_hash = (item.get("file_hash") or "").strip()
                session_id = item.get("session_id")
                download_url = item.get("download_url") or ""
                sim = item["sim"]
                conditions = item.get("conditions") if isinstance(item.get("conditions"), dict) else {}
                
                full_download_url = build_download_url(self.base_url, download_url)
                
                state_key = self._state_key(item)
                url_key = f"{self.base_url}#{sim}-session-{session_id}"

                try:
                    content = self._download_bytes(full_download_url)
                    content_sha1 = sha1_bytes(content)
                    source_sha1 = file_hash or content_sha1
                    source_name = (
                        self._acc_raw_name(item, source_sha1) if sim == "acc"
                        else f"results_evo_session_{session_id}_{source_sha1[:12]}.json"
                    )
                    raw_path = self._raw_dir(sim) / source_name
                    raw_path.write_bytes(content)

                    if sim == "acc":
                        out_path = correct_json_format(
                            str(raw_path), str(self.acc_output_dir), conditions=conditions,
                        )
                        if not out_path:
                            raise ValueError("Conversione JSON ACC non riuscita")
                    else:
                        evo_data = json.loads(content.decode("utf-8-sig", errors="replace"))
                        converted = convert_evo_json(evo_data, source_name, source_sha1)
                        if not converted:
                            skipped_count += 1
                            self.state.mark_hash(state_key, status="skipped", first_seen=now_iso(), output_file="")
                            self.state.mark_url(url_key, status="skipped", last_seen=now_iso(), content_hash=state_key)
                            self.log.info(f"[EVO] Scartato: session_id={session_id} ({item.get('session_type')})")
                            continue
                        converted["__source_tracker_url"] = self.base_url
                        converted["__source_tracker_session_id"] = session_id
                        converted["__source_tracker_imported_at"] = item.get("imported_at")
                        converted["__source_tracker_file_hash"] = file_hash
                        if any(value is not None and value != "" for value in conditions.values()):
                            converted["conditions"] = conditions
                            converted["__conditions_source"] = "evo_server_log"
                        out_path = save_converted_json(converted, str(self.session_json_dir))

                    converted_count += 1
                    self.state.mark_hash(state_key, status="ok", first_seen=now_iso(), output_file=out_path)
                    self.state.mark_url(url_key, status="converted", last_seen=now_iso(), content_hash=state_key)
                    self.log.info(f"[{sim.upper()}] Convertito: session_id={session_id} -> {Path(out_path).name}")

                except Exception as e:
                    failed_count += 1
                    self.state.mark_url(url_key, status="error", last_seen=now_iso(), content_hash=state_key)
                    self.log.error(f"[{sim.upper()}] Errore session_id={session_id}: {e}")

                try:
                    self.state.save()
                except Exception:
                    pass

                for _ in range(max(0, self.sleep_between_downloads_sec)):
                    if self.stop_event.is_set():
                        return
                    time.sleep(1)

            if len(new_items) > self.batch_size:
                self.log.info(f"[WOACC] Batch limit raggiunto: processati {self.batch_size}/{len(new_items)}. Gli altri al prossimo giro.")

            self.log.info(f"[WOACC] Scansione completata | Convertiti: {converted_count} | Scartati: {skipped_count} | Errori: {failed_count}")

        except Exception as e:
            self.log.error(f"[WOACC] Errore controllo tracker: {e}")
