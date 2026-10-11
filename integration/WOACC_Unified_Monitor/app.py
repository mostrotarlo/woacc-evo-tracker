import os
import json
import threading
import time
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from core.logging_gui import setup_logger, attach_queue_to_text_widget
from core.state import StateStore
from providers.acc_provider import AccTrackerMonitor
from providers.evo_provider import EvoTrackerMonitor
from providers.acctracker_provider import ACCTrackerWebMonitor

APP_TITLE = "WOACC Unified Monitor"

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

class App:

    def open_settings(self):
        """Apre una finestra per editare config/app_config.json con validazione + backup."""
        win = tk.Toplevel(self.root)
        win.title("Impostazioni (app_config.json)")
        win.geometry("900x650")

        # Notebook: Editor + Guida
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        tab_edit = ttk.Frame(nb)
        tab_help = ttk.Frame(nb)
        nb.add(tab_edit, text="Config")
        nb.add(tab_help, text="Guida parametri")

        # --- Editor ---
        ttk.Label(tab_edit, text=f"File: {self.cfg_path}").pack(anchor="w")

        txt = scrolledtext.ScrolledText(tab_edit, wrap="none")
        txt.pack(fill="both", expand=True, pady=(8, 8))

        # carica contenuto file
        try:
            raw = self.cfg_path.read_text(encoding="utf-8")
        except Exception as e:
            raw = ""
            messagebox.showerror("Errore", f"Impossibile leggere il file config:\n{e}")

        txt.insert("1.0", raw)

        # --- Pulsanti ---
        btn_row = ttk.Frame(tab_edit)
        btn_row.pack(fill="x")

        def save():
            new_raw = txt.get("1.0", "end-1c")
            # valida JSON
            try:
                parsed = json.loads(new_raw)
            except json.JSONDecodeError as e:
                messagebox.showerror(
                    "JSON non valido",
                    f"Errore JSON:\n{e}\n\nRiga {e.lineno}, colonna {e.colno}"
                )
                return
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante il parsing JSON:\n{e}")
                return

            # backup
            try:
                bak = Path(str(self.cfg_path) + ".bak")
                if self.cfg_path.exists():
                    bak.write_text(self.cfg_path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception as e:
                self.logger.error(f"[APP] Errore backup config: {e}")

            # salva
            try:
                self.cfg_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
                self.cfg = parsed  # aggiorna config in memoria
                self.logger.info("[APP] Config salvata da GUI (Impostazioni).")
                messagebox.showinfo("Salvato", "Config salvata correttamente.\n\nNota: alcune modifiche richiedono riavvio.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Errore salvataggio", f"Impossibile salvare:\n{e}")

        def cancel():
            win.destroy()

        ttk.Button(btn_row, text="Salva", command=save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Annulla", command=cancel).pack(side="left")

        # --- Guida parametri ---
        help_path = self.base_dir / "config" / "app_config.README.md"
        ttk.Label(tab_help, text=f"Guida: {help_path}").pack(anchor="w")

        help_txt = scrolledtext.ScrolledText(tab_help, wrap="word")
        help_txt.pack(fill="both", expand=True, pady=(8, 0))

        if help_path.exists():
            help_txt.insert("1.0", help_path.read_text(encoding="utf-8"))
        else:
            help_txt.insert(
                "1.0",
                "Guida non trovata.\n\nCrea il file config/app_config.README.md per documentare i parametri."
            )
        help_txt.configure(state="disabled")

    def toggle_autostart(self):
        """Aggiorna il config quando cambia la spunta autostart."""
        val = bool(self.autostart_var.get())

        self.cfg.setdefault("app", {})["autostart_monitoring"] = val

        try:
            self.cfg_path.write_text(
                json.dumps(self.cfg, indent=2),
                encoding="utf-8"
            )
            self.logger.info(f"[APP] Autostart monitoraggio impostato a: {val}")
        except Exception as e:
            self.logger.error(f"[APP] Errore salvataggio autostart: {e}")

    def load_saved_base_dir(self) -> str:
        """Legge la BASE salvata in config/base_dir.json (se presente e valida)."""
        try:
            p = Path(__file__).resolve().parent / "config" / "base_dir.json"
            if not p.exists():
                return ""
            data = json.loads(p.read_text(encoding="utf-8"))
            base = (data.get("base_dir") or "").strip()
            return base if base and Path(base).exists() else ""
        except Exception:
            return ""

    def save_base_dir(self, base_dir: str):
        """Salva la BASE in config/base_dir.json."""
        p = Path(__file__).resolve().parent / "config" / "base_dir.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"base_dir": base_dir}, indent=2), encoding="utf-8")

    def ask_base_dir_once(self) -> str:
        """Chiede la BASE solo se non già salvata."""
        saved = self.load_saved_base_dir()
        if saved:
            return saved

        messagebox.showinfo(
            "Cartella BASE",
            "Seleziona la cartella BASE (dove vuoi creare/leggere config, results e output)."
        )
        chosen = filedialog.askdirectory(title="Seleziona cartella BASE") or ""
        if chosen:
            self.save_base_dir(chosen)
        return chosen
    
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("900x620")

        # --- scelta BASE_DIR ---
        self.base_dir = self.ask_base_dir_once()
        if not self.base_dir:
            root.destroy()
            return

        self.base_dir = Path(self.base_dir)
        self.output_root = self.base_dir.parent
        
        # --- carica config ---
        self.cfg_path = self.base_dir / "config" / "app_config.json"
        if not self.cfg_path.exists():
            messagebox.showerror("Config mancante", f"Non trovo {self.cfg_path}")
            root.destroy()
            return

        self.cfg = read_json(self.cfg_path)

        # --- prepara cartelle ---
        self.paths = self.cfg.get("paths", {})
        self.results_dir = self.base_dir / self.paths.get("results_dir", "results")
        self.acc_output_dir = self.output_root / self.paths.get("acc_output_dir", "session_jsons")
        self.evo_output_dir = self.output_root / self.paths.get("evo_output_dir", "session_json_evo")
        self.logs_dir = self.base_dir / self.paths.get("logs_dir", "logs")
        self.state_file = self.base_dir / self.paths.get("state_file", "config/state.json")
        self.urls_file = self.base_dir / self.paths.get("urls_file", "config/urls_acc.txt")
        self.urls_evo_file = self.base_dir / self.paths.get("urls_evo_file", "config/urls_evo.txt")
        self.urls_acctracker_file = self.base_dir / self.paths.get("urls_acctracker_file", "config/urls_acctracker.txt")
        self.acctracker_state_dir = self.base_dir / self.paths.get("acctracker_state_dir", "config/acctracker_state")

        safe_mkdir(self.results_dir)
        safe_mkdir(self.acc_output_dir)
        safe_mkdir(self.evo_output_dir)
        safe_mkdir(self.logs_dir)
        safe_mkdir(self.state_file.parent)
        safe_mkdir(self.urls_file.parent)
        safe_mkdir(self.urls_evo_file.parent)
        safe_mkdir(self.urls_acctracker_file.parent)
        safe_mkdir(self.acctracker_state_dir)

        # --- logging thread-safe ---
        self.log_queue = queue.Queue()
        self.logger = setup_logger(str(self.logs_dir / "app.log"), self.log_queue, debug=bool(self.cfg.get("app", {}).get("debug", False)))

        # --- stato persistente ---
        self.state = StateStore(str(self.state_file))

        # --- UI ---
        self.stop_event = threading.Event()
        self.monitors: list[tuple[str, threading.Thread]] = []

        self.build_ui()
        attach_queue_to_text_widget(self.root, self.log_queue, self.log_output)

        self.logger.info(f"[APP] Base dir: {self.base_dir}")
        self.logger.info(f"[APP] State file: {self.state_file}")

        # autostart opzionale
        if bool(self.cfg.get("app", {}).get("autostart_monitoring", False)):
            if self.load_urls() or self.load_evo_urls() or self.load_acctracker_urls():
                self.start_all_monitoring()
            else:
                self.logger.info("[APP] Autostart attivo ma nessun URL configurato.")

    def ask_base_dir(self) -> str:
        messagebox.showinfo("Cartella BASE", "Seleziona la cartella BASE in cui l'app deve creare/leggere config, results e output.")
        p = filedialog.askdirectory(title="Seleziona cartella BASE")
        return p or ""

    def build_ui(self):
        # Tabs
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True)

        self.tab_acc = ttk.Frame(nb)
        self.tab_evo = ttk.Frame(nb)
        self.tab_acctracker = ttk.Frame(nb)

        nb.add(self.tab_acc, text="ACC")
        nb.add(self.tab_evo, text="AC Evo")
        nb.add(self.tab_acctracker, text="ACCTracker")

        # ---------------- ACC TAB ----------------
        top = ttk.Frame(self.tab_acc)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="URL ACC (una directory web con link .json)").pack(anchor="w")

        row = ttk.Frame(top)
        row.pack(fill="x", pady=6)

        self.url_entry = ttk.Entry(row)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(row, text="Aggiungi", command=self.add_url).pack(side="left")

        self.url_list = tk.Listbox(top, selectmode=tk.MULTIPLE, height=6)
        self.url_list.pack(fill="x", pady=(6, 0))

        # load urls
        for u in self.load_urls():
            self.url_list.insert(tk.END, u)

        btns = ttk.Frame(top)
        btns.pack(fill="x", pady=8)

        ttk.Button(btns, text="Rimuovi selezionati", command=self.remove_selected).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Salva URL", command=self.save_urls).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Avvia monitoraggio", command=self.start_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Stop", command=self.stop_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Impostazioni", command=self.open_settings).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Converti RAW esistenti", command=self.convert_existing).pack(side="left")

        self.process_all_pages_var = tk.BooleanVar(value=False)  # default SOLO prima pagina

        ttk.Checkbutton(
            top,
            text="Elabora tutte le pagine (crawl completo storico)",
            variable=self.process_all_pages_var
        ).pack(anchor="w", pady=(2, 0))

        # --- Autostart checkbox ---
        self.autostart_var = tk.BooleanVar(
            value=bool(self.cfg.get("app", {}).get("autostart_monitoring", False))
        )

        autostart_cb = ttk.Checkbutton(
            top,
            text="Avvia monitoraggio automaticamente all'avvio",
            variable=self.autostart_var,
            command=self.toggle_autostart
        )
        autostart_cb.pack(anchor="w", pady=(6, 0))

        ttk.Label(top, text=f"Output ACC: {self.acc_output_dir}").pack(anchor="w", pady=(6, 0))

        # ---------------- EVO TAB ----------------
        evo = ttk.Frame(self.tab_evo)
        evo.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(
            evo,
            text="Link Tracker EVO / WOACC Tracker",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        ttk.Label(
            evo,
            text="Inserisci la root del tracker, es: https://woacc.zapto.org/tracker. L'app userà automaticamente /api/woacc/sessions.",
            justify="left"
        ).pack(anchor="w", pady=(2, 6))

        evo_row = ttk.Frame(evo)
        evo_row.pack(fill="x", pady=4)

        ttk.Label(evo_row, text="URL:").pack(side="left", padx=(0, 6))
        self.evo_url_entry = ttk.Entry(evo_row)
        self.evo_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        evo_key_row = ttk.Frame(evo)
        evo_key_row.pack(fill="x", pady=4)

        ttk.Label(evo_key_row, text="API Key:").pack(side="left", padx=(0, 6))
        self.evo_api_key_entry = ttk.Entry(evo_key_row)
        self.evo_api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(evo_key_row, text="Aggiungi", command=self.add_evo_url).pack(side="left")

        self.evo_url_list = tk.Listbox(evo, selectmode=tk.MULTIPLE, height=6)
        self.evo_url_list.pack(fill="x", pady=(6, 0))

        for u in self.load_evo_urls():
            self.evo_url_list.insert(tk.END, u)

        evo_btns = ttk.Frame(evo)
        evo_btns.pack(fill="x", pady=8)

        ttk.Button(evo_btns, text="Rimuovi selezionati", command=self.remove_selected_evo).pack(side="left", padx=(0, 8))
        ttk.Button(evo_btns, text="Salva link EVO", command=self.save_evo_urls).pack(side="left", padx=(0, 8))
        ttk.Button(evo_btns, text="Avvia monitoraggio EVO", command=self.start_evo_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(evo_btns, text="Stop", command=self.stop_monitoring).pack(side="left", padx=(0, 8))

        evo_cfg = self.cfg.get("evo", {})
        out_label = self.acc_output_dir if bool(evo_cfg.get("output_to_acc_session_json", True)) else self.evo_output_dir
        ttk.Label(
            evo,
            text=f"Output EVO convertito: {out_label}",
            justify="left"
        ).pack(anchor="w", pady=(8, 0))

        ttk.Label(
            evo,
            text="Compatibile con WOACC Tracker API: /api/woacc/ping, /api/woacc/sessions e /api/woacc/session/<id>/original.json",
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # ---------------- ACCTRACKER TAB ----------------
        tracker = ttk.Frame(self.tab_acctracker)
        tracker.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(tracker, text="Server basati su ACCTracker", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(tracker, text="Inserisci la root del sito; la pagina /Sessions viene rilevata automaticamente.").pack(anchor="w", pady=(2, 6))
        tracker_row = ttk.Frame(tracker)
        tracker_row.pack(fill="x", pady=4)
        ttk.Label(tracker_row, text="URL:").pack(side="left", padx=(0, 6))
        self.acctracker_url_entry = ttk.Entry(tracker_row)
        self.acctracker_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(tracker_row, text="Aggiungi", command=self.add_acctracker_url).pack(side="left")
        self.acctracker_url_list = tk.Listbox(tracker, selectmode=tk.MULTIPLE, height=7)
        self.acctracker_url_list.pack(fill="x", pady=(6, 0))
        for url in self.load_acctracker_urls():
            self.acctracker_url_list.insert(tk.END, url)
        tracker_btns = ttk.Frame(tracker)
        tracker_btns.pack(fill="x", pady=8)
        ttk.Button(tracker_btns, text="Rimuovi selezionati", command=self.remove_selected_acctracker).pack(side="left", padx=(0, 8))
        ttk.Button(tracker_btns, text="Salva URL", command=self.save_acctracker_urls).pack(side="left", padx=(0, 8))
        ttk.Button(tracker_btns, text="Avvia monitoraggio ACCTracker", command=self.start_acctracker_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(tracker_btns, text="Stop tutti", command=self.stop_monitoring).pack(side="left")
        ttk.Label(tracker, text=f"Output JSON WOACC: {self.acc_output_dir}").pack(anchor="w", pady=(8, 0))

        # ---------------- COMANDI GLOBALI ----------------
        global_buttons = ttk.Frame(self.root)
        global_buttons.pack(fill="x", padx=10, pady=(6, 4))
        ttk.Button(global_buttons, text="Avvia tutti i monitor", command=self.start_all_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(global_buttons, text="Stop tutti", command=self.stop_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(global_buttons, text="Impostazioni", command=self.open_settings).pack(side="left")

        # ---------------- LOG ----------------
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        ttk.Label(log_frame, text="Log").pack(anchor="w")
        self.log_output = scrolledtext.ScrolledText(log_frame, height=13)
        self.log_output.pack(fill="both", expand=True)

        # evento apertura tab evo -> log
        def on_tab_changed(event):
            idx = event.widget.index("current")
            if event.widget.tab(idx, "text") == "AC Evo":
                self.logger.info("[EVO] Sezione AC Evo pronta: usa le API WOACC Tracker")
        nb.bind("<<NotebookTabChanged>>", on_tab_changed)

    # ----- URL management -----
    def load_urls(self) -> list[str]:
        if not self.urls_file.exists():
            return []
        lines = self.urls_file.read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines if l.strip()]

    def save_urls(self):
        urls = [self.url_list.get(i) for i in range(self.url_list.size())]
        self.urls_file.write_text("\n".join(urls), encoding="utf-8")
        self.logger.info(f"[APP] Salvati {len(urls)} URL in {self.urls_file}")

    def add_url(self):
        url = (self.url_entry.get() or "").strip()
        if not url:
            return
        self.url_list.insert(tk.END, url)
        self.url_entry.delete(0, tk.END)

    def remove_selected(self):
        sel = list(self.url_list.curselection())
        for i in reversed(sel):
            self.url_list.delete(i)

    # ----- EVO URL management -----
    def parse_evo_source(self, item: str):
        """
        Formato supportato:
          https://tracker.example.com
          https://tracker.example.com | API_KEY
        Mantiene compatibilità con i vecchi urls_evo.txt che contenevano solo URL.
        """
        item = (item or "").strip()
        if "|" in item:
            url, api_key = item.split("|", 1)
            return url.strip(), api_key.strip()
        return item, ""

    def format_evo_source(self, url: str, api_key: str = "") -> str:
        url = (url or "").strip()
        api_key = (api_key or "").strip()
        if api_key:
            return f"{url} | {api_key}"
        return url

    def load_evo_urls(self) -> list[str]:
        if not self.urls_evo_file.exists():
            return []
        lines = self.urls_evo_file.read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines if l.strip()]

    def save_evo_urls(self):
        urls = [self.evo_url_list.get(i) for i in range(self.evo_url_list.size())]
        self.urls_evo_file.write_text("\n".join(urls), encoding="utf-8")
        self.logger.info(f"[EVO] Salvati {len(urls)} link tracker in {self.urls_evo_file}")
    def add_evo_url(self):
        url = (self.evo_url_entry.get() or "").strip()
        api_key = (self.evo_api_key_entry.get() or "").strip()
        if not url:
            return
        self.evo_url_list.insert(tk.END, self.format_evo_source(url, api_key))
        self.evo_url_entry.delete(0, tk.END)
        self.evo_api_key_entry.delete(0, tk.END)

    def remove_selected_evo(self):
        sel = list(self.evo_url_list.curselection())
        for i in reversed(sel):
            self.evo_url_list.delete(i)

    # ----- ACCTracker URL management -----
    def load_acctracker_urls(self) -> list[str]:
        if not self.urls_acctracker_file.exists():
            return []
        return [line.strip() for line in self.urls_acctracker_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    def save_acctracker_urls(self):
        urls = [self.acctracker_url_list.get(i) for i in range(self.acctracker_url_list.size())]
        self.urls_acctracker_file.write_text("\n".join(urls), encoding="utf-8")
        self.logger.info(f"[ACCTRACKER] Salvati {len(urls)} URL")

    def add_acctracker_url(self):
        url = (self.acctracker_url_entry.get() or "").strip()
        if url:
            self.acctracker_url_list.insert(tk.END, url)
            self.acctracker_url_entry.delete(0, tk.END)

    def remove_selected_acctracker(self):
        for i in reversed(self.acctracker_url_list.curselection()):
            self.acctracker_url_list.delete(i)

    # ----- Monitoring -----
    def start_monitoring(self):
        self.save_urls()
        urls = [self.url_list.get(i) for i in range(self.url_list.size())]
        if not urls:
            messagebox.showwarning("Nessun URL", "Aggiungi almeno un URL.")
            return

        self.stop_event.clear()

        app_cfg = self.cfg.get("app", {})
        verify_ssl = bool(app_cfg.get("verify_ssl", False))
        user_agent = str(app_cfg.get("user_agent", "Mozilla/5.0"))
        batch_size = int(app_cfg.get("batch_size", 5))
        check_interval_sec = int(app_cfg.get("check_interval_sec", 1800))
        sleep_between_downloads_sec = int(app_cfg.get("sleep_between_downloads_sec", 2))
        sleep_between_batches_sec = int(app_cfg.get("sleep_between_batches_sec", 240))

        self.logger.info("[APP] ⏱ Avvio monitoraggio ACC...")

        # avvia un monitor per ogni URL
        for url in urls:
            monitor = AccTrackerMonitor(
                base_url=url,
                results_dir=str(self.results_dir),
                acc_output_dir=str(self.acc_output_dir),
                state_store=self.state,
                logger=self.logger,
                verify_ssl=verify_ssl,
                user_agent=user_agent,
                stop_event=self.stop_event,
                batch_size=batch_size,
                check_interval_sec=check_interval_sec,
                sleep_between_downloads_sec=sleep_between_downloads_sec,
                sleep_between_batches_sec=sleep_between_batches_sec,
                process_all_pages=bool(self.process_all_pages_var.get())  # ✅ NEW

            )
            th = threading.Thread(target=monitor.run_forever, daemon=True)
            th.start()
            self.monitors.append((url, th))

        self.logger.info(f"[APP] Monitor attivi: {len(self.monitors)}")

    def start_evo_monitoring(self):
        self.save_evo_urls()
        urls = [self.evo_url_list.get(i) for i in range(self.evo_url_list.size())]
        if not urls:
            messagebox.showwarning("Nessun link EVO", "Aggiungi almeno un link del Tracker EVO.")
            return

        self.stop_event.clear()

        app_cfg = self.cfg.get("app", {})
        evo_cfg = self.cfg.get("evo", {})
        verify_ssl = bool(app_cfg.get("verify_ssl", False))
        user_agent = str(app_cfg.get("user_agent", "Mozilla/5.0"))
        batch_size = int(evo_cfg.get("batch_size", app_cfg.get("batch_size", 5)))
        check_interval_sec = int(evo_cfg.get("check_interval_sec", app_cfg.get("check_interval_sec", 400)))
        sleep_between_downloads_sec = int(app_cfg.get("sleep_between_downloads_sec", 2))
        default_api_key = str(evo_cfg.get("api_key", "") or "")
        api_limit = int(evo_cfg.get("api_limit", 1000))
        output_to_acc = bool(evo_cfg.get("output_to_acc_session_json", True))
        session_json_dir = self.acc_output_dir if output_to_acc else self.evo_output_dir

        self.logger.info("[APP] ⏱ Avvio monitoraggio EVO da WOACC Tracker API...")
        self.logger.info(f"[EVO] Output convertiti: {session_json_dir}")

        for source in urls:
            url, source_api_key = self.parse_evo_source(source)
            api_key = source_api_key or default_api_key
            monitor = EvoTrackerMonitor(
                base_url=url,
                results_dir=str(self.results_dir),
                session_json_dir=str(session_json_dir),
                state_store=self.state,
                logger=self.logger,
                verify_ssl=verify_ssl,
                user_agent=user_agent,
                stop_event=self.stop_event,
                batch_size=batch_size,
                check_interval_sec=check_interval_sec,
                sleep_between_downloads_sec=sleep_between_downloads_sec,
                api_key=api_key,
                api_limit=api_limit,
                acc_output_dir=str(self.acc_output_dir),
                acc_backfill_existing=bool(evo_cfg.get("acc_backfill_existing", False)),
            )
            th = threading.Thread(target=monitor.run_forever, daemon=True)
            th.start()
            self.monitors.append((url, th))

        self.logger.info(f"[APP] Monitor EVO attivi: {len(urls)}")

    def start_acctracker_monitoring(self):
        self.save_acctracker_urls()
        urls = [self.acctracker_url_list.get(i) for i in range(self.acctracker_url_list.size())]
        if not urls:
            messagebox.showwarning("Nessun ACCTracker", "Aggiungi almeno un server ACCTracker.")
            return
        self.stop_event.clear()
        cfg = self.cfg.get("acctracker", {})
        for url in urls:
            monitor = ACCTrackerWebMonitor(
                base_url=url,
                output_dir=str(self.acc_output_dir),
                state_dir=str(self.acctracker_state_dir),
                logger=self.logger,
                stop_event=self.stop_event,
                check_interval_sec=int(cfg.get("check_interval_sec", 1800)),
                bootstrap_sessions=int(cfg.get("bootstrap_sessions", 20)),
                sleep_between_downloads_sec=float(cfg.get("sleep_between_downloads_sec", 1)),
            )
            th = threading.Thread(target=monitor.run_forever, daemon=True)
            th.start()
            self.monitors.append((url, th))
        self.logger.info(f"[APP] Monitor ACCTracker attivi: {len(urls)}")

    def start_all_monitoring(self):
        """Avvia solo le sezioni che hanno almeno una sorgente configurata."""
        if self.load_urls():
            self.start_monitoring()
        if self.load_evo_urls():
            self.start_evo_monitoring()
        if self.load_acctracker_urls():
            self.start_acctracker_monitoring()

    def stop_monitoring(self):
        self.logger.info("[APP] ⛔ Stop richiesto...")
        self.stop_event.set()
        # non joiniamo (daemon), ma svuotiamo lista
        self.monitors.clear()
        try:
            self.state.save()
        except Exception:
            pass
        self.logger.info("[APP] Stop impostato. (I thread si fermeranno al prossimo check/sleep)")

    def convert_existing(self):
        # converte solo RAW presenti sotto results/*/raw/*.json non ancora processati (hash)
        self.logger.info("[APP] 🔁 Conversione RAW esistenti...")
        raw_files = list(self.results_dir.glob("**/raw/*.json"))
        if not raw_files:
            self.logger.info("[APP] Nessun RAW trovato.")
            return

        from providers.acc_provider import correct_json_format, sha256_bytes

        converted = 0
        skipped = 0
        failed = 0

        for p in raw_files:
            try:
                b = p.read_bytes()
                h = sha256_bytes(b)
                if self.state.hash_seen(h):
                    skipped += 1
                    continue

                out_path = correct_json_format(str(p), str(self.acc_output_dir))
                if out_path:
                    self.state.mark_hash(h, status="ok", first_seen=time.strftime("%Y-%m-%dT%H:%M:%S"), output_file=out_path)
                    p.unlink(missing_ok=True)
                    converted += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        try:
            self.state.save()
        except Exception:
            pass

        self.logger.info(f"[APP] Conversione completata: ok={converted}, skipped={skipped}, failed={failed}")

def main():
    root = tk.Tk()
    App(root)
    try:
        root.mainloop()
    finally:
        # best-effort save state
        pass

if __name__ == "__main__":
    main()
