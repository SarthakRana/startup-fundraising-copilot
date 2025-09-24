from typing import List, Dict
from ..tools.search import search_investors_by_hint
from ..tools.fetch import fetch_text
from ..tools.extract import recent_highlights

def run(brief: dict, allow_scrape: bool = False) -> List[Dict]:
    sectors = brief.get("sector", [])
    stage = (brief.get("stage") or "").strip().lower()
    geo = (brief.get("geo") or "").strip()

    # If no signal at all, return empty (API validator should already prevent this)
    if not sectors and not stage and not geo:
        return []

    candidates = search_investors_by_hint(sectors, stage or "seed", geo)

    if allow_scrape:
        for inv in candidates[:20]:
            blobs = []
            for u in inv.get("urls", [])[:3]:
                txt = fetch_text(u)
                if txt:
                    blobs.append(txt)
            if blobs:
                inv["recent_news"] = recent_highlights(" ".join(blobs), max_items=3)
    return candidates
