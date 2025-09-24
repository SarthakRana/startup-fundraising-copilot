import json, os, hashlib
from typing import List, Dict
from ..config import PROJECT_ROOT

SEED_PATH = os.path.join(PROJECT_ROOT, "app", "data", "seed_investors.json")

def _unique_key(inv: Dict) -> str:
    raw = f"{inv.get('name')}|{inv.get('fund')}"
    return hashlib.sha1(raw.encode()).hexdigest()

def load_seed_investors() -> List[Dict]:
    with open(SEED_PATH, "r") as f:
        data = json.load(f)
    for inv in data:
        inv["unique_key"] = _unique_key(inv)
    return data

def search_investors_by_hint(sector_terms: List[str], stage: str) -> List[Dict]:
    data = load_seed_investors()
    sector_terms_lower = {s.lower() for s in sector_terms}
    stage_lower = stage.lower()
    scored = []
    for inv in data:
        inv_sectors = {s.lower() for s in inv.get("sectors", [])}
        inv_stages = {s.lower() for s in inv.get("stages", [])}
        sector_overlap = len(sector_terms_lower & inv_sectors)
        stage_match = 1 if stage_lower in inv_stages else 0
        if sector_overlap or stage_match:
            inv["_seed_sector_overlap"] = sector_overlap
            inv["_seed_stage_match"] = stage_match
            scored.append(inv)
    scored.sort(key=lambda x: (x["_seed_stage_match"], x["_seed_sector_overlap"]), reverse=True)
    return scored[:60]
