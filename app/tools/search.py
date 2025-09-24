import json, os, hashlib, re
from typing import List, Dict
from ..config import PROJECT_ROOT, SERPAPI_API_KEY
from urllib.parse import urlparse

SEED_PATH = os.path.join(PROJECT_ROOT, "app", "data", "seed_investors.json")

def _unique_key(inv: Dict) -> str:
    raw = f"{inv.get('name','')}|{inv.get('fund','')}".strip().lower()
    return hashlib.sha1(raw.encode()).hexdigest()

def load_seed_investors() -> List[Dict]:
    with open(SEED_PATH, "r") as f:
        data = json.load(f)
    for inv in data:
        inv["unique_key"] = _unique_key(inv)
    return data

# ---------- SerpAPI live search ----------
def _query_strings(sectors: List[str], stage: str, geo_hint: str = "") -> List[str]:
    sectors = [s for s in sectors if s]
    stage = (stage or "").strip()
    if not sectors and not stage:
        return []  # no signal -> no queries

    sector_phrase = " ".join(sectors) if sectors else ""
    stage_phrase = stage.replace("-", " ") if stage else ""
    geo_part = f" {geo_hint}" if geo_hint else ""

    queries = []
    if sector_phrase and stage_phrase:
        queries += [
            f"{sector_phrase} {stage_phrase} venture capital{geo_part}",
            f"top {sector_phrase} {stage_phrase} investors{geo_part}",
        ]
    elif sector_phrase:
        queries += [
            f"top {sector_phrase} investors{geo_part}",
            f"{sector_phrase} venture capital firms{geo_part}",
        ]
    elif stage_phrase:
        queries += [
            f"{stage_phrase} venture capital firms{geo_part}",
            f"top {stage_phrase} investors{geo_part}",
        ]
    return queries

def _parse_snippet_for_names(snippet: str) -> List[Dict]:
    out = []
    if not snippet:
        return out
    tokens = re.split(r"[•\-\–\—\|,;]", snippet)
    for t in tokens:
        t = t.strip()
        m = re.search(r"([A-Z][A-Za-z&'\s]+)\s+(Capital|Ventures|Partners|VC)", t)
        if m:
            fund = f"{m.group(1).strip()} {m.group(2)}"
            out.append({"fund": fund})
    return out

def _normalize(inv: Dict, sectors: List[str], stage: str) -> Dict:
    inv = {**inv}
    inv.setdefault("name", inv.get("name") or inv.get("fund") or "Investor")
    inv.setdefault("fund", inv.get("fund") or inv.get("name"))
    inv.setdefault("stages", [stage] if stage else ["seed"])
    inv.setdefault("sectors", sectors or ["ai","infra"])
    inv.setdefault("geo", "global")
    inv.setdefault("urls", inv.get("urls") or [])
    inv.setdefault("notable_investments", [])
    inv.setdefault("recent_news", [])
    inv.setdefault("warm_paths", [])
    inv["unique_key"] = _unique_key(inv)
    return inv

def search_live_investors(sectors: List[str], stage: str, geo_hint: str = "") -> List[Dict]:
    if not SERPAPI_API_KEY:
        return []
    queries = _query_strings(sectors, stage, geo_hint)
    if not queries:
        return []

    try:
        from serpapi import GoogleSearch
    except Exception:
        return []

    results: Dict[str, Dict] = {}
    for q in queries:
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "q": q,
            "num": "10",
            "hl": "en",
            "safe": "active",
        }
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            for item in (data.get("organic_results") or []):
                title = (item.get("title") or "").strip()
                link = item.get("link") or ""
                snippet = (item.get("snippet") or "").strip()

                candidates = []
                m = re.search(r"([A-Z][A-Za-z&'\s]+)\s+(Capital|Ventures|Partners|VC)", title)
                if m:
                    fund = f"{m.group(1).strip()} {m.group(2)}"
                    candidates.append({"fund": fund, "urls": [link]})

                candidates += [{"fund": c.get("fund"), "urls": [link]} for c in _parse_snippet_for_names(snippet)]

                if not candidates and link:
                    host = urlparse(link).netloc.split(".")
                    if len(host) >= 2:
                        guess = host[-2]
                        if guess and guess.isalpha() and len(guess) > 2:
                            candidates.append({"fund": guess.capitalize(), "urls": [link]})

                for c in candidates:
                    inv = _normalize(c, sectors, stage)
                    results[inv["unique_key"]] = inv
        except Exception:
            continue

    return list(results.values())[:80]

def search_investors_by_hint(sector_terms: List[str], stage: str, geo_hint: str = "") -> List[Dict]:
    sector_terms = [s for s in sector_terms if s]
    stage = (stage or "").strip().lower()
    has_signal = bool(sector_terms or stage or geo_hint)

    live = search_live_investors(sector_terms, stage, geo_hint) if has_signal else []
    seed = load_seed_investors() if has_signal else []

    # Filter seed for relevance
    sector_terms_lower = {s.lower() for s in sector_terms}
    seed_scored = []
    if seed:
        for inv in seed:
            inv_sectors = {s.lower() for s in inv.get("sectors", [])}
            inv_stages = {s.lower() for s in inv.get("stages", [])}
            sector_overlap = len(sector_terms_lower & inv_sectors)
            stage_match = 1 if (stage and stage in inv_stages) else 0
            if sector_overlap or stage_match:
                inv["_seed_sector_overlap"] = sector_overlap
                inv["_seed_stage_match"] = stage_match
                seed_scored.append(inv)
        seed_scored.sort(key=lambda x: (x.get("_seed_stage_match",0), x.get("_seed_sector_overlap",0)), reverse=True)

    # Merge + dedupe (prefer entries with URLs)
    merged: Dict[str, Dict] = {}
    for inv in live + seed_scored:
        key = inv.get("unique_key") or _unique_key(inv)
        if key in merged:
            if not merged[key].get("urls") and inv.get("urls"):
                merged[key] = inv
        else:
            merged[key] = inv
    return list(merged.values())
