import csv, os, time
from typing import List, Dict
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from .config import EXPORTS_DIR, NOTION_API_KEY, NOTION_PARENT_PAGE_ID
from notion_client import Client as NotionClient

def export_csv(matches: List[Dict]) -> str:
    ts = int(time.time())
    path = os.path.join(EXPORTS_DIR, f"matches_{ts}.csv")
    cols = ["rank","investor","fund","fit_score","stage_fit","sector_fit","geo_fit","momentum","why_now","warm_paths","urls","email_draft"]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, m in enumerate(matches, start=1):
            inv, sc = m["investor"], m["score"]
            w.writerow([
                i, inv.get("name",""), inv.get("fund",""),
                sc["fit_score"], sc["stage_fit"], sc["sector_fit"], sc["geo_fit"], sc["momentum"],
                sc["rationale"],
                "; ".join(inv.get("warm_paths",[])),
                "; ".join(inv.get("urls",[])),
                m.get("email_draft","").replace("\n"," ")
            ])
    return path

def _wrap(text: str, max_width: int, font_size: int) -> list:
    max_chars = int(max_width / (font_size * 0.55))
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > max_chars:
            out.append(line.rstrip()); line = w + " "
        else:
            line += w + " "
    if line.strip(): out.append(line.rstrip())
    return out

def export_pdf(brief: dict, matches: List[Dict]) -> str:
    ts = int(time.time())
    path = os.path.join(EXPORTS_DIR, f"one_pager_{ts}.pdf")
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    x, y = 50, height - 50

    def write_line(text, size=11, leading=14):
        nonlocal y
        c.setFont("Helvetica", size)
        for line in _wrap(text, width - 100, size):
            if y < 80:
                c.showPage(); y = height - 50; c.setFont("Helvetica", size)
            c.drawString(x, y, line); y -= leading

    def write_header(text): write_line(text, size=16, leading=20)

    write_header(f"{brief['name']} — One Pager")
    write_line(f"One-liner: {brief['one_liner']}")
    write_line(f"Sector: {', '.join(brief.get('sector', []))} · Stage: {brief.get('stage','')} · Geo: {brief.get('geo','N/A')}")
    write_line(""); write_line("Why Now:", size=13)
    write_line(brief.get("ask") or "Raising intros to aligned investors.")
    write_line(""); write_line("Traction:", size=13)
    if brief.get("traction"): [write_line(f"- {t}") for t in brief["traction"][:6]]
    else: write_line("- Early traction with design partners.")
    write_line(""); write_line("Top Target Investors:", size=13)
    for m in matches[:10]:
        inv, sc = m["investor"], m["score"]
        write_line(f"- {inv.get('name')} ({inv.get('fund')}) — {sc['rationale']} (score {sc['fit_score']})")
    c.save(); return path

def export_notion(brief: dict, matches: List[Dict]) -> str:
    if not (NOTION_API_KEY and NOTION_PARENT_PAGE_ID):
        return ""
    client = NotionClient(auth=NOTION_API_KEY)
    title = f"{brief['name']} — Fundraising Targets"
    children = []
    children.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content": f"One-liner: {brief['one_liner']}"}}]}})
    children.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content": f"Sector: {', '.join(brief.get('sector', []))} · Stage: {brief.get('stage','')} · Geo: {brief.get('geo','N/A')}"}}]}})
    children.append({"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Top Target Investors"}}]}})
    for m in matches[:25]:
        inv, sc = m["investor"], m["score"]
        children.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content": f"- {inv.get('name')} ({inv.get('fund')}) — {sc['rationale']} (score {sc['fit_score']})"}}]}})
    page = client.pages.create(
        parent={"type":"page_id","page_id": NOTION_PARENT_PAGE_ID},
        properties={"title": [{"type":"text","text":{"content": title}}]},
        children=children
    )
    return page.get("url","")
