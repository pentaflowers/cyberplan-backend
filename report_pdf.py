"""Render the CyberPlan report structure (report_text.build) to a PDF, Pentaflowers design guide v5."""
from __future__ import annotations

import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

FONTS = Path(__file__).parent / "assets" / "fonts"
for name, file in [("SG", "SpaceGrotesk-Regular.ttf"), ("SG-M", "SpaceGrotesk-Medium.ttf"), ("SG-B", "SpaceGrotesk-Bold.ttf"),
                   ("SM", "SpaceMono-Regular.ttf"), ("SM-B", "SpaceMono-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
pdfmetrics.registerFontFamily("SG", normal="SG", bold="SG-B", italic="SG", boldItalic="SG-B")

INK, BODY, MUTED, SOFT = HexColor("#0D0F22"), HexColor("#2E3350"), HexColor("#4A4F6A"), HexColor("#C9CCD6")
EYEBROW, TAG, GREEN, PANEL, MINERAL = HexColor("#0A7C9C"), HexColor("#3B4A8C"), HexColor("#22663D"), HexColor("#E6E8EE"), HexColor("#F6F5F2")
DOTS = [HexColor("#E0443A"), HexColor("#EDC948"), HexColor("#4C72E6"), HexColor("#4FB872")]

W, H = A4
M = 18 * mm

ST = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="SM-B", fontSize=9, leading=12, textColor=EYEBROW),
    "title": ParagraphStyle("title", fontName="SG-M", fontSize=34, leading=34, textColor=INK),
    "subtitle": ParagraphStyle("subtitle", fontName="SG", fontSize=13, leading=18, textColor=BODY),
    "h1": ParagraphStyle("h1", fontName="SG-M", fontSize=22, leading=25, textColor=INK, spaceBefore=2, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="SG-B", fontSize=11.5, leading=15, textColor=INK, spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", fontName="SG", fontSize=10, leading=14.5, textColor=BODY, spaceAfter=5, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="SG", fontSize=10, leading=14, textColor=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "cite": ParagraphStyle("cite", fontName="SM-B", fontSize=7.5, leading=10.5, textColor=MUTED, spaceAfter=4),
    "ai": ParagraphStyle("ai", fontName="SM-B", fontSize=7, leading=9, textColor=TAG, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName="SG", fontSize=8.8, leading=11.5, textColor=BODY),
    "cellb": ParagraphStyle("cellb", fontName="SG-B", fontSize=8.8, leading=11.5, textColor=INK),
    "cellg": ParagraphStyle("cellg", fontName="SG-B", fontSize=8.8, leading=11.5, textColor=GREEN),
    "head": ParagraphStyle("head", fontName="SM-B", fontSize=7.5, leading=10, textColor=MUTED),
    "kvk": ParagraphStyle("kvk", fontName="SM-B", fontSize=8, leading=11, textColor=MUTED),
    "kvv": ParagraphStyle("kvv", fontName="SG-M", fontSize=10.5, leading=14, textColor=INK),
    "disc": ParagraphStyle("disc", fontName="SG", fontSize=9.5, leading=13.5, textColor=MUTED),
}


def para(text: str, style: str) -> Paragraph:
    return Paragraph(escape(str(text)), ST[style])


def dots(c, x, y, r=2.6, gap=2.2):
    for i, col in enumerate(DOTS):
        cx = x + (i % 2) * (2 * r + gap)
        cy = y - (i // 2) * (2 * r + gap)
        c.setFillColor(col)
        c.circle(cx, cy, r, stroke=0, fill=1)


def table(block: dict, avail: float) -> Table:
    widths = [avail * w for w in block.get("widths", [1 / len(block["head"])] * len(block["head"]))]
    data = [[para(h, "head") for h in block["head"]]]
    sc, pc = block.get("status_col"), block.get("priority_col")
    high_words = {"High", "Alta"}
    ok_words = {"In place", "In atto"}
    for row in block["rows"]:
        cells = []
        for i, v in enumerate(row):
            style = "cell"
            if i == pc and v in high_words:
                style = "cellb"
            if i == sc and v in ok_words:
                style = "cellg"
            cells.append(para(v, style))
        data.append(cells)
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 1, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, INK),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, SOFT),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def kv(block: dict, avail: float) -> Table:
    data = [[para(k, "kvk"), para(v, "kvv")] for k, v in block["rows"]]
    t = Table(data, colWidths=[avail * 0.28, avail * 0.72])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.8, INK),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, SOFT),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def render(report: dict) -> bytes:
    meta = report["meta"]
    buf = io.BytesIO()
    avail = W - 2 * M

    def cover(c, doc):
        c.saveState()
        c.setFillColor(INK)
        c.rect(0, H - 34 * mm, W, 34 * mm, stroke=0, fill=1)
        dots(c, M + 3, H - 15 * mm)
        c.setFillColor(HexColor("#F4F2EC"))
        c.setFont("SG-M", 15)
        c.drawString(M + 18, H - 17.2 * mm, "CyberPlan")
        c.setFillColor(HexColor("#B9BCCE"))
        c.setFont("SM-B", 8.5)
        c.drawString(M + 18 + pdfmetrics.stringWidth("CyberPlan", "SG-M", 15) + 8, H - 17.2 * mm, "by Pentaflowers")
        c.restoreState()

    def later(c, doc):
        c.saveState()
        dots(c, M + 3, H - 10 * mm, r=1.8, gap=1.6)
        c.setFont("SM-B", 7.5)
        c.setFillColor(MUTED)
        c.drawString(M + 14, H - 11 * mm, "CyberPlan")
        c.setStrokeColor(INK)
        c.setLineWidth(0.6)
        c.line(M, H - 14 * mm, W - M, H - 14 * mm)
        c.line(M, 14 * mm, W - M, 14 * mm)
        c.drawString(M, 9.5 * mm, meta["footer"].format(v=meta["rules_version"], p=doc.page))
        c.restoreState()

    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=M,
                          title=f"{meta['title']} — {meta['product']}".strip(" —"), author="Pentaflowers Consulting SAS",
                          subject=meta["subtitle"], creator="CyberPlan")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[Frame(M, M, avail, H - 2 * M - 30 * mm, id="c")], onPage=cover),
        PageTemplate(id="body", frames=[Frame(M, 18 * mm, avail, H - 18 * mm - 18 * mm, id="b")], onPage=later),
    ])

    story = [NextPageTemplate("body"), Spacer(1, 22 * mm),
             para(meta["subtitle"], "eyebrow"), Spacer(1, 6 * mm),
             para(meta["title"], "title"), Spacer(1, 4 * mm)]
    if meta["product"]:
        story += [para(meta["product"], "subtitle"), Spacer(1, 8 * mm)]
    L = meta["labels"]
    story += [kv({"rows": [(L["date"], meta["date"]), (L["rules"], meta["rules_version"])]}, avail), Spacer(1, 10 * mm)]
    disc = Table([[para(meta["disclaimer"], "disc")]], colWidths=[avail])
    disc.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), MINERAL), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 9),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    story += [disc, PageBreak()]

    for i, s in enumerate(report["sections"]):
        head = [para(f"{i + 1:02d}", "eyebrow"), para(s["title"], "h1")]
        flow = []
        for b in s["blocks"]:
            t = b["type"]
            if t == "p":
                flow.append(para(b["text"], "p"))
                if b.get("llm"):
                    flow.append(para(meta["llm_label"], "ai"))
            elif t == "h":
                flow.append(para(b["text"], "h2"))
            elif t == "cite":
                flow.append(para(b["text"], "cite"))
            elif t == "bullets":
                flow += [Paragraph(escape(str(x)), ST["bullet"], bulletText="–") for x in b["items"]]
                flow.append(Spacer(1, 3))
            elif t == "kv":
                flow += [kv(b, avail), Spacer(1, 8)]
            elif t == "table":
                flow += [table(b, avail), Spacer(1, 8)]
        # keep each sub-heading with the block that follows it
        grouped, i2 = [], 0
        while i2 < len(flow):
            f = flow[i2]
            if getattr(f, "style", None) is ST["h2"] and i2 + 1 < len(flow):
                grouped.append(KeepTogether([f, flow[i2 + 1]]))
                i2 += 2
            else:
                grouped.append(f)
                i2 += 1
        story.append(KeepTogether(head + grouped[:1]))
        story += grouped[1:]
        story.append(Spacer(1, 10 * mm))
    doc.build(story)
    return buf.getvalue()
