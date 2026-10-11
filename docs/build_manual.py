"""Build the release manual and reproducible chapter navigation."""
from pathlib import Path
import sys
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted, KeepTogether

from manual_content import LANGUAGES
from manual_translations import TRANSLATIONS

LANGUAGES.update(TRANSLATIONS)
ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text().strip()
OUT = ROOT / "output" / "pdf" / f"WOACC_Tracker_{VERSION}_Manual_IT_EN_FR_ES.pdf"

CODE = {
    "tree_evo": """server_1/
  AssettoCorsaEVOServer.exe
  result/                 <- select this folder
    results_...json
  serverConfig/
    Assetto Corsa EVO Server.txt""",
    "tree_acc": """ACCweb/
  config/
    SERVER_ID/
      accwebConfig.json
      settings.json
      event.json
      results/            <- select this folder
        ...json
      log/
        server.log""",
    "firewall_lan": """New-NetFirewallRule -DisplayName "WOACC Tracker LAN" `
  -Direction Inbound -Action Allow -Protocol TCP `
  -LocalPort 5055 -Profile Private `
  -RemoteAddress LocalSubnet""",
    "caddy_domain": """tracker.example.com {
    reverse_proxy 127.0.0.1:5055
}""",
    "caddy_prefix": """# Inside community.example.com { ... }
redir /tracker /tracker/
handle_path /tracker/* {
    reverse_proxy 127.0.0.1:5055 {
        header_up X-Forwarded-Prefix /tracker
    }
}""",
    "api_routes": """Header: X-WOACC-API-Key: YOUR_PRIVATE_API_KEY
GET /api/woacc/ping
GET /api/woacc/sessions?sim=all&limit=1000
GET /api/woacc/session/123/original.json
# Prepend /tracker when it is the public base path.""",
}


class ManualDoc(SimpleDocTemplate):
    def afterFlowable(self, item):
        bookmark = getattr(item, "bookmark", None)
        if bookmark:
            self.canv.bookmarkPage(bookmark)
            self.canv.addOutlineEntry(item.getPlainText(), bookmark, getattr(item, "outline_level", 0), False)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fonts = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("Manual", str(fonts / "segoeui.ttf")))
    pdfmetrics.registerFont(TTFont("ManualBold", str(fonts / "segoeuib.ttf")))
    pdfmetrics.registerFontFamily("Manual", normal="Manual", bold="ManualBold", italic="Manual", boldItalic="ManualBold")
    ink, green, red = colors.HexColor("#172938"), colors.HexColor("#17613e"), colors.HexColor("#a12b37")
    body = ParagraphStyle("Body", fontName="Manual", fontSize=10.2, leading=14.6, textColor=ink, spaceAfter=7)
    heading = ParagraphStyle("Heading", parent=body, fontName="ManualBold", fontSize=21, leading=26, spaceAfter=16, keepWithNext=True)
    sub = ParagraphStyle("Sub", parent=body, fontName="ManualBold", fontSize=12, leading=16, textColor=green, spaceBefore=7, spaceAfter=6, keepWithNext=True)
    cell = ParagraphStyle("Cell", parent=body, fontSize=9.5, leading=13, spaceAfter=0)
    label = ParagraphStyle("Label", parent=cell, fontName="ManualBold")
    code_style = ParagraphStyle("Code", fontName="Courier", fontSize=8.4, leading=11.5, textColor=ink, spaceAfter=0)
    story = []
    width = A4[0] - 96

    def para(text, style=body):
        return Paragraph(escape(text), style)

    def title(text, bookmark, level=0):
        p = para(text, heading)
        p.bookmark, p.outline_level = bookmark, level
        return p

    def box(item, background, border):
        result = Table([[item]], colWidths=[width])
        result.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1),background),
            ("LINEBEFORE", (0,0),(0,-1),3,border), ("LEFTPADDING",(0,0),(-1,-1),12),
            ("RIGHTPADDING",(0,0),(-1,-1),12), ("TOPPADDING",(0,0),(-1,-1),9),
            ("BOTTOMPADDING",(0,0),(-1,-1),9)]))
        return result

    story.extend([Spacer(1, 85), para("WOACC", ParagraphStyle("Cover1",parent=heading,fontSize=48,leading=54,textColor=green)),
        para("Tracker", ParagraphStyle("Cover2",parent=heading,fontSize=40,leading=46)),
        para(f"Version {VERSION}  |  Windows x64", sub), Spacer(1,26),
        para("Installation & User Manual", ParagraphStyle("Cover3",parent=heading,fontSize=24,leading=30)),
        para("Manuale d'uso  /  User manual  /  Manuel utilisateur  /  Manual de uso"),
        Spacer(1,18), para("ACC + EVO", ParagraphStyle("Sim",parent=sub,fontSize=17,leading=22,textColor=red)),
        para("Windows service · Server discovery · Live timing · Network access · Discord · Bridge API"),
        Spacer(1,40), para("11 October 2026"),
        para("Community-made project. Not official Kunos software."),
        Paragraph('Demo: <link href="https://woacc.zapto.org/tracker/">https://woacc.zapto.org/tracker/</link>', body), PageBreak()])
    story.append(title("Choose your language / Scegli la lingua", "languages"))
    for code, (name, subtitle, chapters) in LANGUAGES.items():
        story.append(Paragraph(f'<link href="#{code}"><b>{escape(name)}</b></link> - {escape(subtitle)}', body))
        story.append(Spacer(1,10))
    story.extend([Spacer(1,25), para("Each language contains the complete fourteen-chapter guide. Technical commands and official references are shared in the final appendix."),
        para("Ogni lingua contiene la guida completa in quattordici capitoli. I comandi e i riferimenti ufficiali sono nell'appendice comune finale."),
        para("Chaque langue comprend les quatorze chapitres complets. Commandes et références officielles dans l'annexe commune."),
        para("Cada idioma incluye los catorce capítulos completos. Comandos y referencias oficiales en el apéndice común."),
        Spacer(1,25), box(para("Examples use reserved example domains and sample IPs. Replace them with your own addresses. No credentials, private database or personal server configuration are included."), colors.HexColor("#edf4f0"), green), PageBreak()])

    for language, (name, subtitle, chapters) in LANGUAGES.items():
        story.append(title(name, language))
        story.append(para(subtitle, sub))
        story.append(para(f"WOACC Tracker {VERSION}"))
        for index, (chapter, _) in enumerate(chapters, 1):
            story.append(Paragraph(f'<link href="#{language}_{index}">{index:02d}. {escape(chapter)}</link>', body))
        story.append(Spacer(1,18))
        story.append(Paragraph('<link href="#appendix">Technical appendix / Appendice / Annexe / Apéndice</link>', body))
        story.append(PageBreak())
        for index, (chapter, content) in enumerate(chapters, 1):
            story.append(title(f"{index:02d}  {chapter}", f"{language}_{index}", 1))
            lines = content.strip().splitlines()
            cursor = 0
            while cursor < len(lines):
                line = lines[cursor].strip()
                cursor += 1
                if not line:
                    continue
                if line.startswith("## "):
                    story.append(para(line[3:], sub))
                elif line.startswith("::"):
                    rows = []
                    while True:
                        left, right = line[2:].split("|", 1)
                        rows.append([para(left,label),para(right,cell)])
                        if cursor >= len(lines) or not lines[cursor].strip().startswith("::"):
                            break
                        line = lines[cursor].strip()
                        cursor += 1
                    table = Table(rows,colWidths=[132,width-132],hAlign="LEFT")
                    table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f0f4f6"),colors.white]),
                        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
                        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
                    story.extend([table,Spacer(1,9)])
                elif line.startswith("```"):
                    key = line[3:]
                    cursor += 1
                    story.extend([box(Preformatted(CODE[key],code_style),colors.HexColor("#edf2f5"),green),Spacer(1,9)])
                elif line.startswith("! "):
                    story.extend([box(para(line[2:]),colors.HexColor("#fff5df"),colors.HexColor("#a16d10")),Spacer(1,8)])
                else:
                    story.append(para(line))
            story.append(PageBreak())

    story.append(title("Technical appendix / Appendice tecnica", "appendix"))
    story.append(para("Caddy - validation and reload / validazione e ricarica",sub))
    story.append(box(Preformatted('.\\caddy.exe validate --config .\\Caddyfile\n.\\caddy.exe reload --config .\\Caddyfile',code_style),colors.HexColor("#edf2f5"),green))
    story.append(Spacer(1,12))
    story.append(para("Run from the Caddy folder. Reload requires a running Caddy instance with its admin endpoint enabled. If Caddy is managed by a Windows service or another launcher, follow that installation's reload/restart procedure. Do not start a second Caddy on the same ports."))
    story.append(para("Eseguire dalla cartella Caddy. Reload richiede Caddy attivo e endpoint amministrativo abilitato. Se gestito come servizio o da un launcher, usare la relativa procedura di riavvio. Non avviare una seconda istanza sulle stesse porte."))
    story.append(para("Depuis le dossier Caddy ; reload nécessite une instance active et son endpoint administrateur. Avec service/launcher, suivre sa procédure. Ne pas démarrer deux instances sur les mêmes ports."))
    story.append(para("Desde carpeta Caddy; reload necesita instancia activa y endpoint administrador. Con servicio/launcher seguir su procedimiento. No iniciar otra instancia en los mismos puertos."))
    story.append(para("Official references / Riferimenti ufficiali / Références / Referencias",sub))
    for name, url in (
        ("Caddy: handle_path and prefix stripping", "https://caddyserver.com/docs/caddyfile/directives/handle_path"),
        ("Caddy: reverse_proxy", "https://caddyserver.com/docs/caddyfile/directives/reverse_proxy"),
        ("Caddy: automatic HTTPS and domain requirements", "https://caddyserver.com/docs/automatic-https"),
        ("Microsoft: Windows Firewall command-line configuration", "https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-with-command-line"),
    ):
        story.append(Paragraph(f'<link href="{url}">{escape(name)}</link>',body))
    story.append(para("Examples checked against the WOACC Tracker release implementation and official documentation on 11 October 2026. Network/firewall changes are not performed by the application."))

    def frame(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(green)
        canvas.rect(48,A4[1]-36,90,3,fill=1,stroke=0)
        canvas.setFillColor(red)
        canvas.rect(140,A4[1]-36,28,3,fill=1,stroke=0)
        canvas.setFont("Manual",8)
        canvas.setFillColor(colors.HexColor("#617480"))
        canvas.drawString(48,A4[1]-52,f"WOACC TRACKER  {VERSION}")
        canvas.drawRightString(A4[0]-48,A4[1]-52,"INSTALLATION & USER MANUAL")
        canvas.setStrokeColor(colors.HexColor("#dbe4e9"))
        canvas.line(48,43,A4[0]-48,43)
        canvas.drawString(48,29,"IT / EN / FR / ES  |  Windows x64")
        canvas.drawRightString(A4[0]-48,29,str(doc.page))
        canvas.restoreState()

    doc = ManualDoc(str(OUT),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=78,bottomMargin=61,
                    title=f"WOACC Tracker {VERSION} - Multilingual User Manual",author="WOACC",subject="Installation, configuration and network access")
    doc.build(story,onFirstPage=frame,onLaterPages=frame)
    print(OUT)


if __name__ == "__main__":
    main()
