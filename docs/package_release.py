"""Assemble a clean Windows release from the complete PyInstaller build."""
import hashlib
import json
import argparse
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text().strip()
DIST = ROOT / "dist_service" / "WOACC Tracker"
RELEASE = ROOT / "release"
STAGING = RELEASE / "staging" / f"WOACC_Tracker_v{VERSION}"
ZIP = RELEASE / f"WOACC_Tracker_v{VERSION}_Windows_x64.zip"
PDF = ROOT / "output" / "pdf" / f"WOACC_Tracker_{VERSION}_Manual_IT_EN_FR_ES.pdf"


def checksum(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-documents", action="store_true", help="Update documentation in an existing staging tree without replacing binaries")
    args = parser.parse_args()
    required = [DIST / "WOACC Tracker.exe", DIST / "_internal" / "python314.dll",
                DIST / "WOACC Tracker Engine" / "WOACC Tracker Engine.exe",
                DIST / "WOACC Tracker Engine" / "_internal" / "python314.dll", PDF]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    if STAGING.exists() and not args.refresh_documents:
        raise FileExistsError(f"Inspect existing staging before rebuilding: {STAGING}")
    STAGING.parent.mkdir(parents=True, exist_ok=True)
    if not STAGING.exists():
        shutil.copytree(DIST, STAGING)
    manual = STAGING / "Manual"
    manual.mkdir(exist_ok=True)
    shutil.copy2(PDF, manual / PDF.name)
    thumbnail = ROOT / "docs/assets/woacc-evo-acc-tracker-15.1.0.png"
    if thumbnail.is_file():
        shutil.copy2(thumbnail, STAGING / "WOACC_EVO_ACC_Tracker.png")
    for source, destination in ((ROOT / "LICENSE", "LICENSE"),
        (ROOT / "VERSION", "VERSION"),
        (ROOT / "docs" / "START_HERE_IT_EN_FR_ES.txt", "START_HERE_IT_EN_FR_ES.txt"),
        (ROOT / "docs" / f"RELEASE_NOTES_{VERSION}.md", "RELEASE_NOTES.md")):
        shutil.copy2(source, STAGING / destination)
    # Only allow packaged dependency assets and explicitly selected public docs.
    forbidden = {"config.json", "running_servers.json", "service.log", "service-control.log"}
    files = sorted(path for path in STAGING.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    for path in files:
        if path.name in forbidden or path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".log", ".dmp"}:
            raise RuntimeError(f"Private runtime data in package: {path}")
    (STAGING / "SHA256SUMS.txt").write_text("\n".join(f"{checksum(path)}  {path.relative_to(STAGING).as_posix()}" for path in files) + "\n", encoding="ascii")
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(STAGING.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(STAGING.parent).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt archive member: {bad}")
        count = len(archive.namelist())
    digest = checksum(ZIP)
    (RELEASE / f"{ZIP.name}.sha256").write_text(f"{digest}  {ZIP.name}\n", encoding="ascii")
    report = {"version": VERSION, "archive": ZIP.name, "files": count, "bytes": ZIP.stat().st_size,
              "sha256": digest, "manual": PDF.name, "private_runtime_files": 0, "zip_integrity": "passed", "published": False}
    (RELEASE / f"verification_{VERSION}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
