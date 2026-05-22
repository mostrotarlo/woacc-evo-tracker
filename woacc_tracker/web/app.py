from functools import wraps
from typing import Any, Dict
from pathlib import Path
import ipaddress
from woacc_tracker.core.importer import Importer

from flask import Flask, abort, flash, jsonify, make_response, redirect, render_template, request, send_file, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from woacc_tracker.core.database import Database
from woacc_tracker.core.security import verify_password
from woacc_tracker.core.utils import ms_to_time, format_gap
from woacc_tracker.core.translations import available_languages, load_vocabulary, pick_language
from woacc_tracker.core.config import save_config, DEFAULT_WOACC_API_KEY


def normalize_base_path(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/")


def create_app(db: Database, cfg: Dict[str, Any]) -> Flask:
    base_path = normalize_base_path(cfg.get("base_path", ""))

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path=f"{base_path}/static" if base_path else "/static"
    )

    app.secret_key = cfg.get("secret_key") or "woacc-tracker-dev-secret-change-me"
    app.config["WOACC_CFG"] = cfg
    app.config["WOACC_DB"] = db
    app.config["APPLICATION_ROOT"] = base_path or "/"

    # WOACC Bridge API v13:
    # enabled by default, protected by the shared ACC_JSON_Monitor_Plus 2 key.
    # Users can opt out from the desktop app by disabling woacc_api_enabled.
    if "woacc_api_enabled" not in cfg:
        cfg["woacc_api_enabled"] = True
    # v13 definitive: shared key expected by ACC_JSON_Monitor_Plus 2.
    # Existing custom/old keys are overwritten so every tracker speaks the same bridge protocol.
    if cfg.get("woacc_api_key") != DEFAULT_WOACC_API_KEY:
        cfg["woacc_api_key"] = DEFAULT_WOACC_API_KEY
        try:
            save_config(cfg)
        except Exception:
            pass
    # Supporto reverse proxy e sottopercorso Caddy, es. /tracker.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    @app.template_filter("lap_time")
    def _lap_time(ms):
        return ms_to_time(ms)

    @app.template_filter("gap")
    def _gap(ms):
        return format_gap(ms)

    @app.context_processor
    def inject_theme_and_i18n():
        lang = pick_language(request, cfg)
        vocab = load_vocabulary(lang)

        def t(key: str, default: str | None = None) -> str:
            return str(vocab.get(key, default if default is not None else key))

        script_root = (request.script_root or "").rstrip("/")
        host = (request.host or "").split(":", 1)[0].lower()
        # In locale diretto (127.0.0.1:PORT) non forziamo cfg.base_path,
        # altrimenti il cambio lingua genera /tracker/set-language e va in 404.
        if host in {"localhost", "127.0.0.1", "::1"} or host.startswith("127."):
            public_base_path = script_root
        else:
            public_base_path = script_root or base_path

        return {
            "theme": cfg.get("theme", {}),
            "lang": lang,
            "languages": available_languages(),
            "t": t,
            "base_path": public_base_path,
        }

    def _safe_local_redirect_target(target: str | None) -> str:
        """Redirect solo verso URL locali e compatibili con il sottopercorso Caddy."""
        target = (target or "").strip()
        script_root = (request.script_root or "").rstrip("/")
        host = (request.host or "").split(":", 1)[0].lower()
        if host in {"localhost", "127.0.0.1", "::1"} or host.startswith("127."):
            public_base_path = script_root
        else:
            public_base_path = script_root or base_path

        if not target or target.startswith("//") or "://" in target:
            return f"{public_base_path}/" if public_base_path else url_for("home")

        if not target.startswith("/"):
            target = "/" + target

        # Se l'app gira sotto /tracker ma il next arriva come /leaderboard o /,
        # lo riportiamo dentro il prefisso pubblico invece di finire sulla root WOACC.
        if public_base_path and not (target == public_base_path or target.startswith(public_base_path + "/")):
            target = public_base_path + target

        return target

    @app.route("/set-language/<lang_code>")
    def set_language(lang_code: str):

        lang_code = (lang_code or "").strip().lower()

        if lang_code not in available_languages():
            abort(404)

        next_url = _safe_local_redirect_target(
            request.args.get("next")
        )

        resp = make_response(
            redirect(next_url)
        )

        # SOLO preferenza browser utente
        resp.set_cookie(
            "woacc_lang",
            lang_code,
            max_age=60*60*24*365,
            samesite="Lax"
        )

        return resp

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if cfg.get("password_enabled") and not session.get("logged_in"):
                return redirect(url_for("login", next=request.path))
            return fn(*args, **kwargs)
        return wrapper

    def local_only_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            remote = (request.remote_addr or "").split(",", 1)[0].strip()
            host = (request.host or "").split(":", 1)[0].strip().lower()
            allowed_hosts = {"localhost", "127.0.0.1", "::1"}
            allowed = host in allowed_hosts or host.startswith("127.") or remote in allowed_hosts or remote.startswith("127.")
            if not allowed:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not cfg.get("password_enabled"):
            session["logged_in"] = True
            return redirect(url_for("home"))
        if request.method == "POST":
            password = request.form.get("password", "")
            if verify_password(password, cfg.get("password_hash", "")):
                session["logged_in"] = True
                return redirect(request.args.get("next") or url_for("home"))
            flash(load_vocabulary(pick_language(request, cfg)).get("wrong_password", "Password errata"))
        return render_template("login.html", cfg=cfg)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login" if cfg.get("password_enabled") else "home"))

    @app.route("/")
    @login_required
    def home():
        stats = db.one(
            """SELECT
                (SELECT COUNT(*) FROM servers) AS servers,
                (SELECT COUNT(*) FROM sessions) AS sessions,
                (SELECT COUNT(DISTINCT track_name) FROM servers) AS tracks,
                (SELECT MAX(session_datetime) FROM sessions) AS last_session
            """
        )
        servers = db.query(
            """SELECT s.*, COUNT(se.id) AS entries_count, COUNT(DISTINCT se.driver_id) AS drivers_count, COUNT(sess.id) AS sessions_count
               FROM servers s
               LEFT JOIN sessions sess ON sess.server_id=s.id
               LEFT JOIN session_entries se ON se.session_id=sess.id
               GROUP BY s.id
               ORDER BY s.last_session_at DESC
               LIMIT 8"""
        )
        sessions = db.query(
            """SELECT sess.*, srv.server_name, srv.track_name
               FROM sessions sess JOIN servers srv ON srv.id=sess.server_id
               ORDER BY sess.session_datetime DESC LIMIT 12"""
        )
        return render_template("home.html", cfg=cfg, stats=stats, servers=servers, sessions=sessions)

    @app.route("/servers")
    @login_required
    def servers():
        q = (request.args.get("q") or "").strip().lower()
        sort = request.args.get("sort") or "last"
        direction = request.args.get("dir") or "desc"
        order_map = {"name": "s.server_name", "track": "s.track_name", "first": "s.first_session_at", "last": "s.last_session_at", "sessions": "sessions_count"}
        order = order_map.get(sort, "s.last_session_at")
        direction_sql = "ASC" if direction == "asc" else "DESC"
        params = []
        where = ""
        if q:
            where = "WHERE lower(s.server_name) LIKE ? OR lower(s.track_name) LIKE ?"
            params.extend([f"%{q}%", f"%{q}%"])
        rows = db.query(
            f"""SELECT s.*, COUNT(sess.id) AS sessions_count
                FROM servers s
                LEFT JOIN sessions sess ON sess.server_id=s.id
                {where}
                GROUP BY s.id
                ORDER BY {order} {direction_sql}""",
            tuple(params),
        )
        return render_template("servers.html", cfg=cfg, servers=rows, q=q, sort=sort, direction=direction)

    @app.route("/server/<int:server_id>")
    @login_required
    def server_detail(server_id: int):
        server = db.one("SELECT * FROM servers WHERE id=?", (server_id,))
        if not server:
            return "Server non trovato", 404
        bests = db.query(
            """SELECT d.display_name, COALESCE(se.driver_category, d.driver_category, '') AS driver_category, se.car_name, MIN(se.best_lap_ms) AS best_lap_ms,
                      SUM(se.laps_total) AS laps_total, SUM(se.laps_valid) AS laps_valid,
                      sess.id AS session_id, sess.session_type, sess.session_datetime
               FROM session_entries se
               JOIN drivers d ON d.id=se.driver_id
               JOIN sessions sess ON sess.id=se.session_id
               WHERE sess.server_id=? AND se.best_lap_ms IS NOT NULL
               GROUP BY se.driver_id, se.car_name
               ORDER BY best_lap_ms ASC""",
            (server_id,),
        )
        sessions_rows = db.query("SELECT * FROM sessions WHERE server_id=? ORDER BY session_datetime DESC", (server_id,))

        source_rows = db.query(
            """SELECT DISTINCT src.*
               FROM import_sources src
               JOIN sessions sess ON sess.source_id=src.id
               WHERE sess.server_id=?
               ORDER BY src.name ASC""",
            (server_id,),
        )

        return render_template(
            "server_detail.html",
            cfg=cfg,
            server=server,
            bests=bests,
            sessions=sessions_rows,
            source_rows=source_rows
        )
    
    @app.route("/sessions")
    @login_required
    def sessions_page():
        q = (request.args.get("q") or "").strip().lower()
        stype = request.args.get("type") or ""
        params = []
        clauses = []
        if q:
            clauses.append("(lower(srv.server_name) LIKE ? OR lower(srv.track_name) LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        if stype:
            clauses.append("sess.session_type=?")
            params.append(stype)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = db.query(
            f"""SELECT sess.*, srv.server_name, srv.track_name
                FROM sessions sess JOIN servers srv ON srv.id=sess.server_id
                {where}
                ORDER BY sess.session_datetime DESC""",
            tuple(params),
        )
        types = db.query("SELECT DISTINCT session_type FROM sessions ORDER BY session_type")
        return render_template("sessions.html", cfg=cfg, sessions=rows, q=q, stype=stype, types=types)

    @app.route("/session/<int:session_id>")
    @login_required
    def session_detail(session_id: int):
        sess = db.one(
            """SELECT sess.*, srv.server_name, srv.track_name, srv.track_layout
               FROM sessions sess JOIN servers srv ON srv.id=sess.server_id WHERE sess.id=?""",
            (session_id,),
        )
        if not sess:
            return "Sessione non trovata", 404
        entries = db.query(
            """SELECT se.*, d.display_name, d.steam_id, d.nation, COALESCE(se.driver_category, d.driver_category, '') AS driver_category
               FROM session_entries se JOIN drivers d ON d.id=se.driver_id
               WHERE se.session_id=?
               ORDER BY se.position IS NULL, se.position ASC, se.best_lap_ms IS NULL, se.best_lap_ms ASC""",
            (session_id,),
        )
        laps_by_entry = {}
        for e in entries:
            laps_by_entry[e["id"]] = db.query("SELECT * FROM laps WHERE entry_id=? ORDER BY lap_number ASC", (e["id"],))
        return render_template("session_detail.html", cfg=cfg, sess=sess, entries=entries, laps_by_entry=laps_by_entry)

    @app.route("/leaderboard")
    @login_required
    def leaderboard():
        """Classifica aggregata filtrando le sessioni per nome server e pista.

        Uso tipico:
        - server_q=season IV
        - track=COTA
        Il risultato prende il miglior giro valido di ogni pilota/auto nelle sessioni filtrate.
        """
        server_q = (request.args.get("server_q") or "").strip()
        track = (request.args.get("track") or "").strip()
        stype = (request.args.get("type") or "").strip()

        track_clauses = []
        track_params = []
        if server_q:
            track_clauses.append("lower(srv.server_name) LIKE ?")
            track_params.append(f"%{server_q.lower()}%")
        track_where = "WHERE " + " AND ".join(track_clauses) if track_clauses else ""
        tracks = db.query(
            f"""SELECT srv.track_name, COUNT(sess.id) AS sessions_count
                FROM servers srv
                JOIN sessions sess ON sess.server_id=srv.id
                {track_where}
                GROUP BY srv.track_name
                ORDER BY srv.track_name ASC""",
            tuple(track_params),
        )

        clauses = ["se.best_lap_ms IS NOT NULL"]
        params = []
        if server_q:
            clauses.append("lower(srv.server_name) LIKE ?")
            params.append(f"%{server_q.lower()}%")
        if track:
            clauses.append("srv.track_name = ?")
            params.append(track)
        if stype:
            clauses.append("sess.session_type = ?")
            params.append(stype)
        where = "WHERE " + " AND ".join(clauses)

        rows = db.query(
            f"""WITH filtered AS (
                    SELECT
                        se.*,
                        d.display_name,
                        d.nation,
                        COALESCE(se.driver_category, d.driver_category, '') AS driver_category,
                        sess.id AS session_id,
                        sess.session_type,
                        sess.session_datetime,
                        srv.server_name,
                        srv.track_name
                    FROM session_entries se
                    JOIN drivers d ON d.id=se.driver_id
                    JOIN sessions sess ON sess.id=se.session_id
                    JOIN servers srv ON srv.id=sess.server_id
                    {where}
                ), totals AS (
                    SELECT
                        driver_id,
                        car_name,
                        SUM(laps_total) AS laps_total,
                        SUM(laps_valid) AS laps_valid,
                        COUNT(DISTINCT session_id) AS sessions_count
                    FROM filtered
                    GROUP BY driver_id, car_name
                ), best_rows AS (
                    SELECT
                        filtered.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY filtered.driver_id, filtered.car_name
                            ORDER BY filtered.best_lap_ms ASC, filtered.session_datetime DESC
                        ) AS rn
                    FROM filtered
                )
                SELECT
                    best_rows.display_name,
                    best_rows.nation,
                    best_rows.driver_category,
                    best_rows.car_name,
                    best_rows.best_lap_ms,
                    totals.laps_total,
                    totals.laps_valid,
                    totals.sessions_count,
                    best_rows.session_id,
                    best_rows.session_type,
                    best_rows.session_datetime,
                    best_rows.server_name,
                    best_rows.track_name
                FROM best_rows
                JOIN totals ON totals.driver_id=best_rows.driver_id AND totals.car_name=best_rows.car_name
                WHERE best_rows.rn=1
                ORDER BY best_rows.best_lap_ms ASC, best_rows.display_name ASC""",
            tuple(params),
        )
        types = db.query("SELECT DISTINCT session_type FROM sessions ORDER BY session_type")
        return render_template(
            "leaderboard.html",
            cfg=cfg,
            rows=rows,
            tracks=tracks,
            types=types,
            server_q=server_q,
            track=track,
            stype=stype,
        )

    @app.route("/records")
    @login_required
    def records():
        selected_track = (request.args.get("track") or "").strip()
        selected_layout = (request.args.get("layout") or "").strip()
        selected_car = (request.args.get("car") or "").strip()

        tracks = db.query(
            """
            SELECT
                srv.track_name,
                COALESCE(srv.track_layout, '') AS track_layout,
                COUNT(DISTINCT sess.id) AS sessions_count,
                COUNT(DISTINCT se.driver_id) AS drivers_count,
                COUNT(DISTINCT se.car_name) AS cars_count,
                MIN(l.lap_time_ms) AS best_lap_ms
            FROM servers srv
            JOIN sessions sess ON sess.server_id = srv.id
            JOIN session_entries se ON se.session_id = sess.id
            JOIN laps l ON l.entry_id = se.id
            WHERE l.is_valid = 1
              AND srv.track_name IS NOT NULL
              AND srv.track_name <> ''
            GROUP BY srv.track_name, COALESCE(srv.track_layout, '')
            ORDER BY srv.track_name ASC, COALESCE(srv.track_layout, '') ASC
            """
        )

        cars = []
        rows = []
        current_track = None

        if selected_track:
            current_track = db.one(
                """
                SELECT
                    srv.track_name,
                    COALESCE(srv.track_layout, '') AS track_layout,
                    COUNT(DISTINCT sess.id) AS sessions_count,
                    COUNT(DISTINCT se.driver_id) AS drivers_count,
                    COUNT(DISTINCT se.car_name) AS cars_count,
                    MIN(l.lap_time_ms) AS best_lap_ms
                FROM servers srv
                JOIN sessions sess ON sess.server_id = srv.id
                JOIN session_entries se ON se.session_id = sess.id
                JOIN laps l ON l.entry_id = se.id
                WHERE l.is_valid = 1
                  AND srv.track_name = ?
                  AND COALESCE(srv.track_layout, '') = ?
                GROUP BY srv.track_name, COALESCE(srv.track_layout, '')
                """,
                (selected_track, selected_layout),
            )

            cars = db.query(
                """
                SELECT se.car_name, COUNT(DISTINCT se.driver_id) AS drivers_count, MIN(l.lap_time_ms) AS best_lap_ms
                FROM servers srv
                JOIN sessions sess ON sess.server_id = srv.id
                JOIN session_entries se ON se.session_id = sess.id
                JOIN laps l ON l.entry_id = se.id
                WHERE l.is_valid = 1
                  AND srv.track_name = ?
                  AND COALESCE(srv.track_layout, '') = ?
                  AND se.car_name IS NOT NULL
                  AND se.car_name <> ''
                GROUP BY se.car_name
                ORDER BY se.car_name ASC
                """,
                (selected_track, selected_layout),
            )

            params = [selected_track, selected_layout]
            car_filter = ""
            if selected_car:
                car_filter = "AND se.car_name = ?"
                params.append(selected_car)

            rows = db.query(
                f"""
                WITH ranked AS (
                    SELECT
                        d.id AS driver_id,
                        d.display_name,
                        d.nation,
                        d.driver_category,
                        se.car_name,
                        l.lap_time_ms AS best_lap_ms,
                        l.lap_number,
                        sess.id AS session_id,
                        sess.session_type,
                        sess.session_datetime,
                        srv.server_name,
                        srv.track_name,
                        COALESCE(srv.track_layout, '') AS track_layout,
                        ROW_NUMBER() OVER (
                            PARTITION BY d.id, se.car_name
                            ORDER BY l.lap_time_ms ASC, sess.session_datetime DESC, l.lap_number ASC
                        ) AS rn
                    FROM servers srv
                    JOIN sessions sess ON sess.server_id = srv.id
                    JOIN session_entries se ON se.session_id = sess.id
                    JOIN drivers d ON d.id = se.driver_id
                    JOIN laps l ON l.entry_id = se.id
                    WHERE l.is_valid = 1
                      AND srv.track_name = ?
                      AND COALESCE(srv.track_layout, '') = ?
                      {car_filter}
                )
                SELECT *
                FROM ranked
                WHERE rn = 1
                ORDER BY best_lap_ms ASC, display_name ASC, car_name ASC
                """,
                tuple(params),
            )

        return render_template(
            "records.html",
            cfg=cfg,
            tracks=tracks,
            cars=cars,
            rows=rows,
            selected_track=selected_track,
            selected_layout=selected_layout,
            selected_car=selected_car,
            current_track=current_track,
        )



    @app.route("/licenses")
    @login_required
    def licenses_page():
        q = (request.args.get("q") or "").strip().lower()
        mode = (request.args.get("mode") or "ranking").strip().lower()
        clauses = []
        params = []
        if q:
            clauses.append("lower(driver_name) LIKE ?")
            params.append(f"%{q}%")
        where = "WHERE " + " AND ".join(clauses) if clauses else ""

        ranking = db.query(
            f"""SELECT la.*, sess.session_type, sess.session_datetime, srv.track_name, srv.server_name
                FROM license_achievements la
                LEFT JOIN sessions sess ON sess.id=la.session_id
                LEFT JOIN servers srv ON srv.id=sess.server_id
                {where}
                ORDER BY la.license_rank DESC, la.best_time_ms ASC, la.driver_name ASC""",
            tuple(params),
        )
        latest = db.query(
            f"""SELECT la.*, sess.session_type, sess.session_datetime, srv.track_name, srv.server_name
                FROM license_achievements la
                LEFT JOIN sessions sess ON sess.id=la.session_id
                LEFT JOIN servers srv ON srv.id=sess.server_id
                {where}
                ORDER BY la.updated_at DESC
                LIMIT 100""",
            tuple(params),
        )
        return render_template("licenses.html", cfg=cfg, q=q, mode=mode, ranking=ranking, latest=latest)

    @app.route("/logs")
    @login_required
    @local_only_required
    def logs():
        rows = db.query("SELECT * FROM import_files ORDER BY imported_at DESC LIMIT 300")
        return render_template("logs.html", cfg=cfg, rows=rows)

    @app.route("/logs/retry/<int:file_id>", methods=["POST"])
    @login_required
    @local_only_required
    def retry_import_file(file_id: int):
        row = db.one("SELECT * FROM import_files WHERE id=?", (file_id,))
        if not row:
            flash("File log non trovato")
            return redirect(url_for("logs"))

        file_path = Path(row["file_path"])
        source_id = row["source_id"]

        if not file_path.exists():
            flash(f"File non trovato: {file_path}")
            return redirect(url_for("logs"))

        # Rimuove il vecchio record del log per forzare la rilettura.
        # L'importer normalmente salta i file già presenti tramite file_hash.
        db.execute("DELETE FROM import_files WHERE id=?", (file_id,))

        importer = Importer(db, log=print)
        result = importer.import_file(file_path, source_id)

        if result == "imported":
            flash("Rilettura forzata completata: importato correttamente")
        elif result == "skipped":
            flash("Rilettura forzata completata: file saltato. Controlla il motivo nei log.")
        elif result == "error":
            flash("Rilettura forzata completata: ERRORE. Apri i log per vedere il dettaglio completo.")
        else:
            flash(f"Rilettura forzata completata: {result}")

        return redirect(url_for("logs"))


    @app.route("/woacc-community")
    @login_required
    def woacc_community():
        def _is_local_host(hostname: str) -> bool:
            h = (hostname or "").strip().lower()
            if h in {"localhost", "127.0.0.1", "::1"}:
                return True
            try:
                ip = ipaddress.ip_address(h)
                return bool(ip.is_loopback or ip.is_private or ip.is_link_local)
            except Exception:
                return False

        def _request_is_local() -> bool:
            # Con ProxyFix attivo, request.remote_addr usa X-Forwarded-For se arriva da Caddy.
            # Da remoto quindi risulta l'IP reale del client; in locale resta 127.0.0.1/LAN.
            remote = (request.remote_addr or "").split(",", 1)[0].strip()
            host = (request.host or "").split(":", 1)[0].strip()
            return _is_local_host(remote) or _is_local_host(host)

        woacc_main_url = (cfg.get("woacc_main_url") or "https://woacc.zapto.org/").strip()
        if not _request_is_local():
            return redirect(woacc_main_url)

        def _normalize_public_tracker_url(value: str) -> str:
            value = (value or "").strip().rstrip("/")
            if not value:
                return ""
            if not value.startswith(("http://", "https://")):
                value = "http://" + value if ":" in value.split("/", 1)[0] else "https://" + value
            bp = normalize_base_path(cfg.get("base_path", ""))
            if bp and not value.rstrip("/").endswith(bp):
                value += bp
            return value.rstrip("/")

        script_root = (request.script_root or "").rstrip("/")
        public_base_path = script_root or base_path

        configured_public_url = _normalize_public_tracker_url(cfg.get("public_url", ""))
        request_host = (request.host or "").split(":", 1)[0]

        if configured_public_url:
            tracker_url = configured_public_url
            tracker_url_source = "configured"
        elif not _is_local_host(request_host):
            tracker_url = (request.url_root.rstrip("/") + (public_base_path or "")).rstrip("/")
            tracker_url_source = "detected"
        else:
            tracker_url = ""
            tracker_url_source = "missing"

        base_message = (cfg.get("woacc_request_message") or "").strip() or "Ciao Fabio, vorrei collegare il mio WOACC Tracker EVO al WOACC globale. Indirizzo tracker da aggiungere:"
        request_message = base_message
        if tracker_url:
            request_message = f"{base_message} {tracker_url}".strip()

        return render_template(
            "woacc_community.html",
            cfg=cfg,
            tracker_url=tracker_url,
            tracker_url_source=tracker_url_source,
            woacc_url=woacc_main_url,
            discord_url=(cfg.get("woacc_discord_url") or "https://discord.com/channels/@me").strip(),
            discord_contact=(cfg.get("woacc_discord_contact") or "Fabio / WOACC").strip(),
            request_message=request_message,
        )



    # ============================================================
    # WOACC BRIDGE API
    # ============================================================
    # Questi endpoint rendono il Tracker una "costola" di WOACC:
    # - il Tracker continua a monitorare/importare i JSON originali
    # - WOACC può interrogare l'indice e scaricare i JSON completi
    # - WOACC poi li elabora con il suo parser centrale

    def woacc_api_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not cfg.get("woacc_api_enabled", True):
                return jsonify({"ok": False, "error": "WOACC API disabled"}), 403

            api_key = (cfg.get("woacc_api_key") or DEFAULT_WOACC_API_KEY).strip()
            provided = (
                request.headers.get("X-WOACC-API-Key")
                or request.args.get("api_key")
                or ""
            ).strip()

            if provided != api_key:
                return jsonify({"ok": False, "error": "Unauthorized"}), 401

            return fn(*args, **kwargs)
        return wrapper

    def api_url_for(endpoint: str, **values) -> str:
        """
        Restituisce SEMPRE URL relativo pulito (senza duplicare /tracker).
        Il monitor si occupa di aggiungere il base_url.
        """
        return url_for(endpoint, **values)

    @app.route("/api/woacc/ping")
    @woacc_api_required
    def woacc_api_ping():
        return jsonify({
            "ok": True,
            "service": "WOACC Tracker",
            "community_name": cfg.get("community_name", "WOACC Tracker"),
            "base_path": base_path,
            "api_version": 1,
        })

    @app.route("/api/woacc/sessions")
    @woacc_api_required
    def woacc_api_sessions():
        """
        Indice dei JSON originali disponibili.

        Query utili lato WOACC:
        - ?status=imported      default: solo JSON importati correttamente dal Tracker
        - ?status=all           include anche skipped/error
        - ?after=ISO_DATE       filtra per data importazione
        - ?limit=500            limite risultati, max 5000
        """
        status = (request.args.get("status") or "imported").strip().lower()
        after = (request.args.get("after") or "").strip()
        try:
            limit = int(request.args.get("limit") or 1000)
        except ValueError:
            limit = 1000
        limit = max(1, min(limit, 5000))

        clauses = []
        params = []

        if status != "all":
            clauses.append("f.status=?")
            params.append(status)

        if after:
            clauses.append("f.imported_at > ?")
            params.append(after)

        where = "WHERE " + " AND ".join(clauses) if clauses else ""

        rows = db.query(
            f"""SELECT
                    f.id AS import_file_id,
                    f.file_hash,
                    f.file_path,
                    f.status,
                    f.reason,
                    f.imported_at,
                    f.session_id,
                    src.id AS source_id,
                    src.name AS source_name,
                    sess.session_name,
                    sess.session_type,
                    sess.session_datetime,
                    sess.is_completed,
                    sess.laps_total,
                    sess.drivers_count,
                    srv.server_name,
                    srv.track_name,
                    srv.track_layout
                FROM import_files f
                LEFT JOIN import_sources src ON src.id=f.source_id
                LEFT JOIN sessions sess ON sess.id=f.session_id
                LEFT JOIN servers srv ON srv.id=sess.server_id
                {where}
                ORDER BY f.imported_at DESC
                LIMIT ?""",
            tuple(params + [limit]),
        )

        items = []
        for r in rows:
            session_id = r["session_id"]
            file_hash = r["file_hash"]
            download_url = None
            if session_id:
                download_url = api_url_for("woacc_api_original_json", session_id=int(session_id))

            items.append({
                "import_file_id": r["import_file_id"],
                "session_id": session_id,
                "file_hash": file_hash,
                "status": r["status"],
                "reason": r["reason"],
                "imported_at": r["imported_at"],
                "source_id": r["source_id"],
                "source_name": r["source_name"],
                "server_name": r["server_name"],
                "track_name": r["track_name"],
                "track_layout": r["track_layout"],
                "session_name": r["session_name"],
                "session_type": r["session_type"],
                "session_datetime": r["session_datetime"],
                "is_completed": bool(r["is_completed"]) if r["is_completed"] is not None else None,
                "laps_total": r["laps_total"],
                "drivers_count": r["drivers_count"],
                "download_url": download_url,
            })

        return jsonify({
            "ok": True,
            "api_version": 1,
            "count": len(items),
            "items": items,
        })

    @app.route("/api/woacc/session/<int:session_id>/original.json")
    @woacc_api_required
    def woacc_api_original_json(session_id: int):
        row = db.one(
            """SELECT sess.id, sess.file_hash, sess.file_path
               FROM sessions sess
               WHERE sess.id=?""",
            (session_id,),
        )
        if not row:
            abort(404, description="Sessione non trovata")

        path = Path(row["file_path"])
        if not path.exists() or not path.is_file():
            abort(404, description="File JSON originale non trovato sul Tracker")

        # Evita di servire file non JSON se il DB fosse stato alterato manualmente.
        if path.suffix.lower() != ".json":
            abort(403, description="Tipo file non consentito")

        return send_file(
            path,
            mimetype="application/json",
            as_attachment=False,
            download_name=f"woacc_session_{session_id}_{row['file_hash'][:12]}.json",
            max_age=0,
        )

    return app
