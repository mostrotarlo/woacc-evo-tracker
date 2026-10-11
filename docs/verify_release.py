"""Verify every packaged file against its SHA-256 manifest."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text().strip()
ZIP = ROOT / "release" / f"WOACC_Tracker_v{VERSION}_Windows_x64.zip"
PREFIX = f"WOACC_Tracker_v{VERSION}/"
with zipfile.ZipFile(ZIP) as archive:
    manifest = archive.read(PREFIX + "SHA256SUMS.txt").decode("ascii").splitlines()
    for line in manifest:
        digest, name = line.split("  ", 1)
        assert hashlib.sha256(archive.read(PREFIX + name)).hexdigest() == digest, name
    pdf = f"WOACC_Tracker_{VERSION}_Manual_IT_EN_FR_ES.pdf"
    assert archive.read(PREFIX + "Manual/" + pdf) == (ROOT / "output/pdf" / pdf).read_bytes()
    assert archive.read(PREFIX + "VERSION").decode().strip() == VERSION
    assert archive.testzip() is None
print(f"Verified {len(manifest)} packaged file hashes, final manual, version and ZIP integrity.")
