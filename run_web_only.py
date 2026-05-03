from pathlib import Path
from woacc_tracker.core.config import load_config, save_config
from woacc_tracker.core.database import Database
from woacc_tracker.core.importer import Importer
from woacc_tracker.web.app import create_app

if __name__ == "__main__":
    cfg = load_config()
    db = Database(cfg["database_path"])
    db.init_schema()
    importer = Importer(db)
    for source in cfg.get("sources", []):
        if source.get("enabled", True):
            importer.import_folder(Path(source["path"]), source.get("name") or source["path"])
    save_config(cfg)
    app = create_app(db, cfg)
    host = "0.0.0.0" if cfg.get("remote_access") else "127.0.0.1"
    app.run(host=host, port=int(cfg.get("port", 5055)), debug=False, use_reloader=False)
