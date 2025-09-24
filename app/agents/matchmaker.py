from typing import List, Dict

WEIGHTS = {"stage": 0.40, "sector": 0.35, "geo": 0.15, "momentum": 0.10}
def _norm(x): return max(0.0, min(1.0, float(x)))

# Canonical equivalence groups for loose matching
_EQUIV = {
    "pre-seed": {"angel", "pre-seed"},
    "seed": {"seed", "seed+", "pre-series-a"},
    "series-a": {"pre-series-a", "series-a"},
    "series-b": {"series-b"},
    "series-c": {"series-c"},
}

def _canon_stage(s: str) -> str:
    s = (s or "").lower().replace("_", "-").replace(" ", "-")
    # normalize common variants
    if s in {"preseed", "pre-seed"}: s = "pre-seed"
    elif s in {"pre-series-a", "pre-seriesa", "pre-series-a"}: s = "pre-series-a"
    elif s in {"series-a", "seriesa"}: s = "series-a"
    elif s in {"series-b", "seriesb"}: s = "series-b"
    elif s in {"series-c", "seriesc"}: s = "series-c"
    return s

def _stage_match(user_stage: str, inv_stages: set) -> float:
    """
    Returns a stage fitness in [0..1] with loose equivalence.
    """
    if not user_stage:
        return 0.0
    u = _canon_stage(user_stage)
    inv = {_canon_stage(x) for x in inv_stages}

    if u in inv:
        return 1.0
    # loose equivalence (e.g., seed ~ seed+ ~ pre-series-a)
    for canon, group in _EQUIV.items():
        if u in group and (group & inv):
            return 0.75
    # adjacent stages get small credit
    adj = {
        "pre-seed": {"seed"},
        "seed": {"pre-seed", "pre-series-a", "series-a"},
        "pre-series-a": {"seed", "series-a"},
        "series-a": {"pre-series-a", "series-b"},
        "series-b": {"series-a", "series-c"},
        "series-c": {"series-b"},
    }
    if any(s in inv for s in adj.get(u, set())):
        return 0.4
    return 0.0

def score_one(brief: dict, inv: Dict) -> Dict:
    stage = (brief.get("stage") or "").lower()
    sectors = {s.lower() for s in brief.get("sector", [])}
    geo = (brief.get("geo") or "").lower()

    inv_stages = {s.lower() for s in inv.get("stages", [])}
    inv_sectors = {s.lower() for s in inv.get("sectors", [])}
    inv_geo = (inv.get("geo") or "").lower()
    momentum = 1.0 if inv.get("recent_news") else 0.5

    stage_fit = _stage_match(stage, inv_stages)
    sector_fit = len(sectors & inv_sectors) / max(1, len(sectors)) if sectors else 0.0
    geo_fit = 1.0 if (not geo or geo in inv_geo or inv_geo in geo) else 0.5 if inv_geo in ["remote","global","us/eu"] else 0.0

    total = (
        WEIGHTS["stage"] * _norm(stage_fit) +
        WEIGHTS["sector"] * _norm(sector_fit) +
        WEIGHTS["geo"] * _norm(geo_fit) +
        WEIGHTS["momentum"] * _norm(momentum)
    )
    fit_score = round(100 * total, 1)

    bits = []
    if stage_fit >= 0.9: bits.append("stage aligns")
    elif stage_fit >= 0.7: bits.append("nearby stage")
    if sector_fit >= 0.5: bits.append("sector overlap")
    if geo_fit >= 0.9:   bits.append("geo fit")
    if inv.get("recent_news"): bits.append("recent activity")
    rationale = ", ".join(bits) or "general thesis alignment"

    return {
        "fit_score": fit_score,
        "stage_fit": round(stage_fit,2),
        "sector_fit": round(sector_fit,2),
        "geo_fit": round(geo_fit,2),
        "momentum": round(momentum,2),
        "rationale": rationale,
    }

def run(brief: dict, investors: List[Dict]) -> List[Dict]:
    out = []
    for inv in investors:
        inv_copy = dict(inv)
        inv_copy["_score"] = score_one(brief, inv)
        out.append(inv_copy)
    out.sort(key=lambda x: x["_score"]["fit_score"], reverse=True)
    return out
