import socket
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn

from .core.config import load_config, save_config, DEFAULT_WOACC_API_KEY
from .core.translations import available_languages, load_vocabulary, DEFAULT_LANGUAGE
from .core.database import Database
from .core.importer import Importer
from .core.monitor import FolderMonitor
from .core.security import hash_password
from .web.app import create_app


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class TrackerDesktop:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WOACC Tracker v13")
        self.root.geometry("1150x760")
        self.cfg = load_config()
        self.languages = available_languages()
        self.lang = (self.cfg.get("language") or DEFAULT_LANGUAGE).lower()
        if self.lang not in self.languages:
            self.lang = DEFAULT_LANGUAGE
        self.vocab = load_vocabulary(self.lang)
        self.db = Database(self.cfg["database_path"])
        self.db.init_schema()
        self.importer = Importer(self.db, self._log_safe)
        self.monitor = None
        self.httpd = None
        self.server_thread = None
        self.running = False
        self._build_ui()
        self._load_sources_to_tree()
        self._log(self._t("desktop_ready", "Application ready"))


    def _t(self, key: str, default: str = None) -> str:
        return str(self.vocab.get(key, default if default is not None else key))

    def _language_values(self):
        return [f"{code} - {name}" for code, name in self.languages.items()]

    def _language_display(self, code: str) -> str:
        return f"{code} - {self.languages.get(code, code.upper())}"

    def _language_from_display(self, value: str) -> str:
        return (value.split(" - ", 1)[0] or DEFAULT_LANGUAGE).strip().lower()

    def _on_language_change(self, event=None):
        new_lang = self._language_from_display(self.language_var.get())
        if new_lang not in self.languages or new_lang == self.lang:
            return
        self.lang = new_lang
        self.cfg["language"] = new_lang
        save_config(self.cfg)
        self.vocab = load_vocabulary(new_lang)
        self._build_ui()
        self._load_sources_to_tree()
        self.refresh_stats()
        if self.running:
            self.status_var.set(self._t("desktop_status_active", "ACTIVE"))
        self._log(self._t("desktop_language_saved", "Language saved"))

    def _log_safe(self, msg: str):
        try:
            self._log(msg)
        except Exception:
            print(msg)

    def _build_ui(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(self._t("desktop_window_title", "WOACC Tracker"))
        self.status_var = tk.StringVar(value=self._t("desktop_status_stopped", "STOPPED"))
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="WOACC Tracker", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.status_var, foreground="red", font=("Segoe UI", 12, "bold")).pack(side="right")

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=8)
        self.tab_main = ttk.Frame(nb, padding=10)
        self.tab_sources = ttk.Frame(nb, padding=10)
        self.tab_theme = ttk.Frame(nb, padding=10)
        self.tab_logs = ttk.Frame(nb, padding=10)
        nb.add(self.tab_main, text=self._t("desktop_tab_general", "General"))
        nb.add(self.tab_sources, text=self._t("desktop_tab_sources", "Monitored folders"))
        nb.add(self.tab_theme, text=self._t("desktop_tab_theme", "Web theme"))
        nb.add(self.tab_logs, text=self._t("logs", "Logs"))

        self._build_main_tab()
        self._build_sources_tab()
        self._build_theme_tab()
        self._build_logs_tab()

    def _build_main_tab(self):
        frm = self.tab_main
        general = ttk.LabelFrame(frm, text=self._t("desktop_configuration", "Configuration"), padding=12)
        general.pack(fill="x")
        self.community_var = tk.StringVar(value=self.cfg.get("community_name", "WOACC Tracker"))
        self.port_var = tk.IntVar(value=int(self.cfg.get("port", 5055)))
        self.remote_var = tk.BooleanVar(value=bool(self.cfg.get("remote_access")))
        self.public_url_var = tk.StringVar(value=self.cfg.get("public_url", ""))
        self.base_path_var = tk.StringVar(value=self.cfg.get("base_path", ""))
        self.password_enabled_var = tk.BooleanVar(value=bool(self.cfg.get("password_enabled")))
        self.woacc_share_var = tk.BooleanVar(value=bool(self.cfg.get("woacc_api_enabled", True)))
        self.password_var = tk.StringVar(value="")
        self.scan_interval_var = tk.IntVar(value=int(self.cfg.get("scan_interval_sec", 10)))
        self.language_var = tk.StringVar(value=self._language_display(self.lang))

        language_combo = ttk.Combobox(general, textvariable=self.language_var, values=self._language_values(), width=24, state="readonly")
        language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        rows = [
            (self._t("desktop_community_name", "Community name"), ttk.Entry(general, textvariable=self.community_var, width=55)),
            (self._t("desktop_web_port", "Web app port"), ttk.Entry(general, textvariable=self.port_var, width=12)),
            (self._t("desktop_scan_interval", "Scan interval (sec)"), ttk.Entry(general, textvariable=self.scan_interval_var, width=12)),
            (self._t("desktop_public_url", "Optional public URL"), ttk.Entry(general, textvariable=self.public_url_var, width=55)),
            (self._t("desktop_base_path", "Reverse proxy base path"), ttk.Entry(general, textvariable=self.base_path_var, width=24)),
            (self._t("language", "Language"), language_combo),
        ]
        for i, (label, widget) in enumerate(rows):
            ttk.Label(general, text=label).grid(row=i, column=0, sticky="w", pady=5)
            widget.grid(row=i, column=1, sticky="w", pady=5, padx=8)
        ttk.Label(general, text=self._t("desktop_base_path_hint", "e.g. /tracker if you use Caddy under https://domain/tracker")).grid(row=4, column=2, sticky="w", pady=5)
        ttk.Checkbutton(general, text=self._t("desktop_remote_access", "Remote / LAN access (bind 0.0.0.0)"), variable=self.remote_var).grid(row=6, column=1, sticky="w", pady=5)
        ttk.Checkbutton(general, text=self._t("desktop_woacc_share", "Share data with WOACC (Bridge API enabled)"), variable=self.woacc_share_var).grid(row=7, column=1, sticky="w", pady=5)
        ttk.Label(general, text=self._t("desktop_woacc_share_hint", "Enabled by default. Disable only if you do not want ACC_JSON_Monitor_Plus 2 to import this tracker.")).grid(row=7, column=2, sticky="w", pady=5)
        ttk.Checkbutton(general, text=self._t("desktop_password_protect", "Protect web app with password"), variable=self.password_enabled_var).grid(row=8, column=1, sticky="w", pady=5)
        ttk.Label(general, text=self._t("desktop_new_password", "New password (leave empty to keep current)")).grid(row=9, column=0, sticky="w", pady=5)
        ttk.Entry(general, textvariable=self.password_var, show="*", width=35).grid(row=9, column=1, sticky="w", pady=5, padx=8)

        actions = ttk.LabelFrame(frm, text=self._t("desktop_actions", "Actions"), padding=12)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text=self._t("desktop_start_tracker", "🟢 Start Tracker"), command=self.start_tracker).pack(side="left", padx=5)
        ttk.Button(actions, text=self._t("desktop_stop_tracker", "🔴 Stop Tracker"), command=self.stop_tracker).pack(side="left", padx=5)
        ttk.Button(actions, text=self._t("desktop_open_web", "🌐 Open Web App"), command=self.open_web).pack(side="left", padx=5)
        ttk.Button(actions, text=self._t("desktop_join_woacc", "🌍 Entra nella community WOACC"), command=self.open_woacc_community).pack(side="left", padx=5)
        ttk.Button(actions, text=self._t("desktop_import_now", "📥 Import now"), command=self.manual_import).pack(side="left", padx=5)
        ttk.Button(actions, text=self._t("desktop_save_settings", "💾 Save settings"), command=self.save_settings).pack(side="left", padx=5)

        urls = ttk.LabelFrame(frm, text="URL", padding=12)
        urls.pack(fill="x", pady=5)
        self.urls_text = tk.Text(urls, height=5, wrap="word")
        self.urls_text.pack(fill="x")
        self._update_urls()

        stats = ttk.LabelFrame(frm, text=self._t("desktop_database_status", "Database status"), padding=12)
        stats.pack(fill="x", pady=8)
        self.stats_var = tk.StringVar(value="")
        ttk.Label(stats, textvariable=self.stats_var).pack(anchor="w")
        ttk.Button(stats, text=self._t("desktop_refresh_status", "Refresh status"), command=self.refresh_stats).pack(anchor="w", pady=6)
        self.refresh_stats()



    def _build_sources_tab(self):
        top = ttk.Frame(self.tab_sources)
        top.pack(fill="x", pady=(0, 8))

        ttk.Button(top,text=self._t("desktop_add_folder", "➕ Add folder"),command=self.add_source).pack(side="left", padx=4)
        ttk.Button(top,text=self._t("desktop_edit_name", "✏️ Edit name"),command=self.edit_source_name).pack(side="left", padx=4)
        ttk.Button(top,text=self._t("desktop_remove", "❌ Remove"),command=self.remove_source).pack(side="left", padx=4)
        ttk.Button(top,text=self._t("desktop_toggle", "Enable/Disable"),command=self.toggle_source).pack(side="left", padx=4)

        ttk.Button(
            top,
            text=self._t("desktop_configure_discord_records", "🏁 Configure Discord records"),
            command=self.configure_record_source
        ).pack(side="left", padx=4)

        ttk.Button(
            top,
            text=self._t("desktop_edit_webhook", "🔗 Edit webhook"),
            command=self.edit_source_webhook
        ).pack(side="left", padx=4)

        ttk.Button(
            top,
            text=self._t("desktop_weekly_recap_toggle", "📊 Weekly recap ON/OFF"),
            command=self.toggle_weekly_recap
        ).pack(side="left", padx=4)


        self.sources_tree = ttk.Treeview(
            self.tab_sources,
            columns=(
                "enabled",
                "record",
                "weekly",
                "name",
                "path",
                "announce",
                "webhook"
            ),
            show="headings",
            height=18
        )

        for col,label,width in [
            ("enabled", self._t("desktop_enabled", "Enabled"), 70),
            ("record", self._t("records", "Records"), 80),
            ("weekly", self._t("desktop_recap", "Recap"), 80),
            ("name", self._t("desktop_name", "Name"), 180),
            ("path", self._t("desktop_path", "Path"), 460),
            ("announce", self._t("desktop_announce_name", "Announcement name"), 180),
            ("webhook", self._t("desktop_webhook", "Webhook"), 110),
        ]:
            self.sources_tree.heading(col,text=label)
            self.sources_tree.column(col,width=width)

        self.sources_tree.pack(fill="both", expand=True)

    def _build_theme_tab(self):
        theme = self.cfg.get("theme", {})
        self.theme_vars = {}

        color_presets = [
            "",
            "#0b0f14",
            "#141b24",
            "#101720",
            "#263241",
            "#e8eef6",
            "#93a4b8",
            "#2fd17c",
            "#ff5c5c",
            "#f7c948",
            "#e10600",
            "#0099ff",
            "#ffffff",
            "#000000"
        ]

        font_presets = [
            "Segoe UI, Arial, sans-serif",
            "Arial, sans-serif",
            "Verdana, sans-serif",
            "Tahoma, sans-serif",
            "Trebuchet MS, sans-serif",
            "Roboto, Arial, sans-serif"
        ]

        fields = [
            ("font_family", self._t("desktop_font", "Font"), "font"),
            ("font_size", self._t("desktop_font_size", "Font size"), "number"),
            ("background", self._t("desktop_background", "Background"), "color"),
            ("card", self._t("desktop_card", "Card"), "color"),
            ("card2", self._t("desktop_secondary_card", "Secondary card"), "color"),
            ("line", self._t("desktop_lines", "Lines"), "color"),
            ("text", self._t("desktop_text", "Text"), "color"),
            ("muted", self._t("desktop_muted_text", "Secondary text"), "color"),
            ("accent", self._t("desktop_accent", "Accent"), "color"),
            ("danger", self._t("desktop_error", "Error"), "color"),
            ("warn", self._t("desktop_warning", "Warning"), "color"),
        ]

        frame = ttk.LabelFrame(self.tab_theme, text=self._t("desktop_web_appearance", "Web App appearance"), padding=12)
        frame.pack(fill="x")

        for i, (key, label, kind) in enumerate(fields):
            var = tk.StringVar(value=str(theme.get(key, "")))
            self.theme_vars[key] = var

            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=4)

            if kind == "color":
                combo = ttk.Combobox(frame, textvariable=var, values=color_presets, width=40)
                combo.grid(row=i, column=1, sticky="w", pady=4, padx=8)
                ttk.Label(frame, text=self._t("desktop_list_or_hex", "List or manual HEX")).grid(row=i, column=2, sticky="w")

            elif kind == "font":
                combo = ttk.Combobox(frame, textvariable=var, values=font_presets, width=40)
                combo.grid(row=i, column=1, sticky="w", pady=4, padx=8)
                ttk.Label(frame, text=self._t("desktop_list_or_font", "List or manual font")).grid(row=i, column=2, sticky="w")

            else:
                ttk.Entry(frame, textvariable=var, width=42).grid(row=i, column=1, sticky="w", pady=4, padx=8)

        ttk.Button(frame, text=self._t("desktop_save_theme", "Save theme"), command=self.save_settings).grid(
            row=len(fields),
            column=1,
            sticky="w",
            pady=10
        )

        
    def _build_logs_tab(self):
        self.log_text = tk.Text(self.tab_logs, wrap="word")
        self.log_text.pack(fill="both", expand=True)

    def _log(self, msg: str):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    def _load_sources_to_tree(self):
        self.sources_tree.delete(*self.sources_tree.get_children())

        for idx, src in enumerate(self.cfg.get("sources", [])):

            webhook = self._t("desktop_set", "Set") if src.get("discord_webhook_url") else "—"

            self.sources_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    self._t("yes", "Yes") if src.get("enabled",True) else self._t("no", "No"),
                    self._t("yes", "Yes") if src.get("announce_records") else self._t("no", "No"),
                    self._t("yes", "Yes") if src.get("weekly_recap_enabled") else self._t("no", "No"),
                    src.get("name",""),
                    src.get("path",""),
                    src.get("announce_name",""),
                    webhook
                )
            )

    def save_settings(self):
        self.cfg["community_name"] = self.community_var.get().strip() or "WOACC Tracker"
        self.cfg["port"] = int(self.port_var.get())
        self.cfg["remote_access"] = bool(self.remote_var.get())
        self.cfg["public_url"] = self.public_url_var.get().strip()
        self.cfg["base_path"] = self.base_path_var.get().strip()
        self.cfg["password_enabled"] = bool(self.password_enabled_var.get())
        self.cfg["woacc_api_enabled"] = bool(self.woacc_share_var.get())
        self.cfg["woacc_api_key"] = (self.cfg.get("woacc_api_key") or DEFAULT_WOACC_API_KEY).strip() or DEFAULT_WOACC_API_KEY
        self.cfg["scan_interval_sec"] = int(self.scan_interval_var.get())
        self.cfg["language"] = self._language_from_display(self.language_var.get())
        self.cfg.setdefault("theme", {})
        for k, v in self.theme_vars.items():
            val = v.get().strip()
            self.cfg["theme"][k] = int(val) if k == "font_size" and val.isdigit() else val
        if self.password_var.get():
            self.cfg["password_hash"] = hash_password(self.password_var.get())
            self.password_var.set("")
        if self.cfg["password_enabled"] and not self.cfg.get("password_hash"):
            messagebox.showwarning(self._t("desktop_missing_password", "Missing password"), self._t("desktop_missing_password_detail", "You enabled password protection, but no password is set."))
        save_config(self.cfg)
        self._update_urls()
        self._log(self._t("desktop_settings_saved", "Settings saved"))

    def add_source(self):
        path = filedialog.askdirectory(title=self._t("desktop_select_results_folder", "Select EVO results folder"))
        if not path:
            return

        name = simpledialog.askstring(
            self._t("desktop_source_name", "Source name"),
            self._t("desktop_source_name_prompt", "Source name:"),
            initialvalue=Path(path).name
        ) or Path(path).name

        self.cfg.setdefault("sources", []).append({
            "name": name,
            "path": path,
            "enabled": True,

            "announce_records": False,
            "announce_name": name,
            "discord_webhook_url": "",
            "record_window_started_at": "",

            "weekly_recap_enabled": False,
            "weekly_recap_started_at": ""
        })

        save_config(self.cfg)
        self._load_sources_to_tree()

    def _selected_source_index(self):
        sel = self.sources_tree.selection()
        return int(sel[0]) if sel else None

    def edit_source_name(self):
        idx = self._selected_source_index()
        if idx is None: return
        src = self.cfg["sources"][idx]
        name = simpledialog.askstring(self._t("desktop_source_name", "Source name"), self._t("desktop_new_name", "New name:"), initialvalue=src.get("name", ""))
        if name:
            src["name"] = name
            src.setdefault("announce_name", name)
            save_config(self.cfg)
            self._load_sources_to_tree()

    def remove_source(self):
        idx = self._selected_source_index()
        if idx is None: return
        if messagebox.askyesno(self._t("desktop_confirm", "Confirm"), self._t("desktop_remove_source_confirm", "Remove selected source?")):
            self.cfg["sources"].pop(idx)
            save_config(self.cfg)
            self._load_sources_to_tree()

    def toggle_source(self):
        idx = self._selected_source_index()
        if idx is None: return
        self.cfg["sources"][idx]["enabled"] = not self.cfg["sources"][idx].get("enabled", True)
        save_config(self.cfg)
        self._load_sources_to_tree()

    def configure_record_source(self):
        idx = self._selected_source_index()
        if idx is None:
            return

        src = self.cfg["sources"][idx]

        enable = messagebox.askyesno(
            self._t("desktop_announce_records", "Announce records"),
            self._t("desktop_announce_records_prompt", "Enable record announcements for this folder?\n\nThis is not retroactive.")
        )

        src["announce_records"] = bool(enable)

        if enable:
            src["announce_name"] = simpledialog.askstring(
                self._t("desktop_announce_name", "Announcement name"),
                self._t("desktop_event_server_name", "Event/server name:"),
                initialvalue=src.get("announce_name") or src.get("name", "")
            ) or src.get("name", "")

            current = src.get("discord_webhook_url", "")

            if not current:
                src["discord_webhook_url"] = simpledialog.askstring(
                    self._t("desktop_discord_webhook", "Discord Webhook"),
                    self._t("desktop_discord_webhook_url", "Discord webhook URL:"),
                    initialvalue=""
                ) or ""
            else:
                if messagebox.askyesno(self._t("desktop_webhook", "Webhook"), self._t("desktop_webhook_exists_prompt", "Webhook already present.\nModify it?")):
                    src["discord_webhook_url"] = simpledialog.askstring(
                        self._t("desktop_discord_webhook", "Discord Webhook"),
                        self._t("desktop_new_webhook", "New webhook:"),
                        initialvalue=current
                    ) or current

            src["record_window_started_at"] = datetime.now().isoformat(timespec="seconds")

        else:
            src["record_window_started_at"] = ""
            src["weekly_recap_enabled"] = False
            src["weekly_recap_started_at"] = ""

        save_config(self.cfg)
        self._load_sources_to_tree()
        self._log(self._t("desktop_record_status_log", "Discord records {state} for {name}").format(state=(self._t("desktop_active", "active") if enable else self._t("desktop_disabled", "disabled")), name=src.get("name")))


    def edit_source_webhook(self):
        idx = self._selected_source_index()
        if idx is None:
            return

        src = self.cfg["sources"][idx]

        new_webhook = simpledialog.askstring(
            self._t("desktop_edit_webhook_title", "Edit webhook"),
            self._t("desktop_discord_webhook_url", "Discord webhook URL:"),
            initialvalue=src.get("discord_webhook_url", "")
        )

        if new_webhook is None:
            return

        src["discord_webhook_url"] = new_webhook.strip()
        save_config(self.cfg)
        self._load_sources_to_tree()
        self._log(self._t("desktop_webhook_updated", "Webhook updated for {name}").format(name=src.get("name")))


    def toggle_weekly_recap(self):
        idx = self._selected_source_index()
        if idx is None:
            return

        src = self.cfg["sources"][idx]

        if not src.get("announce_records"):
            messagebox.showwarning(self._t("desktop_records_not_active", "Records not active"), self._t("desktop_enable_records_first", "Enable record announcements first."))
            return

        if not src.get("discord_webhook_url"):
            messagebox.showwarning(self._t("desktop_missing_webhook", "Missing webhook"), self._t("desktop_configure_webhook_first", "Configure the webhook first."))
            return

        enabled = not bool(src.get("weekly_recap_enabled"))
        src["weekly_recap_enabled"] = enabled

        if enabled:
            src["weekly_recap_started_at"] = datetime.now().isoformat(timespec="seconds")
        else:
            src["weekly_recap_started_at"] = ""

        save_config(self.cfg)
        self._load_sources_to_tree()

        self._log(self._t("desktop_weekly_recap_status", "Weekly recap {state} for {name}").format(state=(self._t("desktop_active", "active") if enabled else self._t("desktop_disabled", "disabled")), name=src.get("name")))

    def _update_urls(self):
        port = int(self.port_var.get()) if str(self.port_var.get()).isdigit() else self.cfg.get("port", 5055)
        local = f"http://127.0.0.1:{port}"
        lan = f"http://{self._get_lan_ip()}:{port}"
        public = self.public_url_var.get().strip() or "—"
        base = self.base_path_var.get().strip()
        self.urls_text.delete("1.0", "end")
        share_status = self._t("desktop_enabled", "Enabled") if self.cfg.get("woacc_api_enabled", True) else self._t("desktop_disabled", "Disabled")
        self.urls_text.insert("end", f"{self._t('desktop_local', 'Local')}: {local}\nLAN:    {lan}\nBase path: {base or '/'}\n{self._t('desktop_public_ddns', 'Public/DDNS')}: {public}\nWOACC Bridge API: {share_status}\n")

    def _get_lan_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def refresh_stats(self):
        row = self.db.one("SELECT (SELECT COUNT(*) FROM servers) servers, (SELECT COUNT(*) FROM sessions) sessions, (SELECT COUNT(*) FROM drivers) drivers, (SELECT COUNT(*) FROM laps) laps, (SELECT COUNT(*) FROM record_windows) records")
        self.stats_var.set(f"Server: {row['servers']} | {self._t('sessions', 'Sessions')}: {row['sessions']} | {self._t('drivers', 'Drivers')}: {row['drivers']} | {self._t('laps', 'Laps')}: {row['laps']} | {self._t('event_records', 'Event records')}: {row['records']}")

    def manual_import(self):
        self.save_settings()
        stats_total = {"found": 0, "imported": 0, "skipped": 0, "errors": 0}
        for src in self.cfg.get("sources", []):
            if not src.get("enabled", True):
                continue
            stats = self.importer.import_folder(Path(src["path"]), src.get("name") or Path(src["path"]).name, src)
            for k in stats_total:
                stats_total[k] += stats[k]
            self._log(f"Import {src['path']}: {stats}")
        self.refresh_stats()
        messagebox.showinfo(self._t("desktop_import_completed", "Import completed"), str(stats_total))

    def start_tracker(self):
        if self.running:
            return
        self.save_settings()
        if not any(s.get("enabled", True) for s in self.cfg.get("sources", [])):
            if not messagebox.askyesno(self._t("desktop_no_folder", "No folder"), self._t("desktop_no_active_folders_prompt", "There are no active folders. Start only the web app?")):
                return
        try:
            app = create_app(self.db, self.cfg)
            host = "0.0.0.0" if self.cfg.get("remote_access") else "127.0.0.1"
            port = int(self.cfg.get("port", 5055))
            self.httpd = make_server(host, port, app, server_class=ThreadedWSGIServer)
            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()
            self.monitor = FolderMonitor(self.importer, lambda: self.cfg.get("sources", []), int(self.cfg.get("scan_interval_sec", 10)), self._log)
            self.monitor.scan_once()
            self.monitor.start()
            self.running = True
            self.status_var.set(self._t("desktop_status_active", "ACTIVE"))
            self._log(self._t("desktop_web_started", "Web app started on {host}:{port}").format(host=host, port=port))
            self.refresh_stats()
        except OSError as exc:
            messagebox.showerror(self._t("desktop_start_error", "Startup error"), self._t("desktop_start_error_detail", "Unable to start the web server. Port busy or invalid.\n{exc}").format(exc=exc))
        except Exception as exc:
            messagebox.showerror(self._t("desktop_start_error", "Startup error"), str(exc))

    def stop_tracker(self):
        if self.monitor:
            self.monitor.stop()
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        self.running = False
        self.status_var.set(self._t("desktop_status_stopped", "STOPPED"))
        self._log(self._t("desktop_tracker_stopped", "Tracker stopped"))

    def open_woacc_community(self):
        public_url = (self.public_url_var.get() or self.cfg.get("public_url", "") or "").strip()
        if not public_url:
            messagebox.showwarning(
                self._t("desktop_public_url_missing_title", "Public URL missing"),
                self._t(
                    "desktop_public_url_missing_detail",
                    "Before requesting WOACC integration, set the Public URL in the desktop app.\n\n"
                    "Examples:\n"
                    "https://yourdomain.com/tracker\n"
                    "http://PUBLIC_IP:5055\n\n"
                    "How to find it:\n"
                    "1) If you use Caddy/DDNS, use the public HTTPS address, for example https://yourname.ddns.net/tracker.\n"
                    "2) If you expose the tracker directly, use http://YOUR_PUBLIC_IP:PORT.\n"
                    "3) Test it from a phone not connected to your Wi-Fi before sending the request.\n\n"
                    "The Public URL must be reachable from outside your local network."
                )
            )
            return
        port = int(self.cfg.get("port", 5055))
        webbrowser.open(f"http://127.0.0.1:{port}/woacc-community")

    def open_web(self):
        port = int(self.cfg.get("port", 5055))
        webbrowser.open(f"http://127.0.0.1:{port}")


def main():
    root = tk.Tk()
    app = TrackerDesktop(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_tracker(), root.destroy()))
    root.mainloop()
