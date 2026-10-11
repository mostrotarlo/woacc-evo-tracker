"""Render all manual pages and produce contact sheets for visual review."""
from pathlib import Path
import json

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text().strip()
PDF = ROOT / "output" / "pdf" / f"WOACC_Tracker_{VERSION}_Manual_IT_EN_FR_ES.pdf"
OUT = ROOT / "tmp" / "pdfs"
OUT.mkdir(parents=True, exist_ok=True)
reader = PdfReader(PDF)
assert len(reader.pages) == 63, len(reader.pages)
chapter_groups = [item for item in reader.outline if isinstance(item, list)]
assert len(chapter_groups) == 4 and all(len(group) == 14 for group in chapter_groups)
texts = [page.extract_text() or "" for page in reader.pages]
text = "\n".join(texts)
assert all(name in text for name in ("Italiano", "English", "Français", "Español"))
assert "C:\\Users\\mostr" not in text
assert "HEXA" not in text
overflow = []
with pdfplumber.open(PDF) as document:
    for number, page in enumerate(document.pages, 1):
        bad = [char for char in page.chars if char["x0"] < 46 or char["x1"] > page.width - 46 or char["top"] < 24 or char["bottom"] > page.height - 24]
        if bad:
            overflow.append((number, "".join(char["text"] for char in bad)))
assert not overflow, overflow
document = pdfium.PdfDocument(str(PDF))
for number, page in enumerate(document, 1):
    bitmap = page.render(scale=1.3)
    bitmap.to_pil().save(OUT / f"page-{number:02d}.png")
    bitmap.close()
    page.close()
document.close()
for start in range(1, len(reader.pages) + 1, 12):
    sheet = Image.new("RGB", (1200, 1780), "#dce3e7")
    draw = ImageDraw.Draw(sheet)
    for slot, number in enumerate(range(start, min(start + 12, len(reader.pages) + 1))):
        with Image.open(OUT / f"page-{number:02d}.png") as page:
            page.thumbnail((280, 400))
            x, y = 10 + (slot % 4) * 300, 30 + (slot // 4) * 580
            sheet.paste(page, (x, y))
            draw.text((x, y - 18), f"Page {number}", fill="#172938")
    sheet.save(OUT / f"contact-{start:02d}.png")
report = {"pages": len(reader.pages), "languages": ["it", "en", "fr", "es"], "chapters_per_language": 14, "boundary_overflows": overflow, "links": sum(len(page.get("/Annots", [])) for page in reader.pages)}
(OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
