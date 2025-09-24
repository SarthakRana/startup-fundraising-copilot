from typing import Dict, List
from .agents import researcher, matchmaker
from .exports import export_csv, export_pdf, export_notion

def one_pager_md(brief: dict, matches: List[Dict]) -> str:
    lines = [
        f"# {brief['name']} — One Pager",
        f"**One-liner:** {brief['one_liner']}",
        f"**Sector:** {', '.join(brief.get('sector', []))} · **Stage:** {brief.get('stage','')} · **Geo:** {brief.get('geo','N/A')}",
        "", "## Why Now", "- " + (brief.get("ask") or "Raising intros to aligned investors."), "", "## Traction"
    ]
    if brief.get("traction"): lines += [f"- {t}" for t in brief["traction"][:5]]
    else: lines.append("- Early traction with design partners.")
    lines += ["", "## Top Target Investors (Why)"]
    for m in matches[:10]:
        inv, sc = m["investor"], m["score"]
        lines.append(f"- **{inv.get('name')} ({inv.get('fund')})** — {sc['rationale']} (score {sc['fit_score']})")
    return "\n".join(lines)

def run_pipeline(brief: dict, top_k: int = 25, use_llm: bool = True, allow_scrape: bool = False, exports: List[str] = ["csv"]):
    # research & rank
    candidates = researcher.run(brief, allow_scrape=allow_scrape)
    ranked = matchmaker.run(brief, candidates)

    # assemble matches WITHOUT email_draft (on-demand later)
    matches: List[Dict] = []
    for inv in ranked[:top_k]:
        matches.append({
            "investor": {
                "name": inv.get("name",""),
                "fund": inv.get("fund",""),
                "stages": inv.get("stages",[]),
                "sectors": inv.get("sectors",[]),
                "check_min": inv.get("check_min"),
                "check_max": inv.get("check_max"),
                "geo": inv.get("geo"),
                "notable_investments": inv.get("notable_investments",[]),
                "recent_news": inv.get("recent_news",[]),
                "urls": inv.get("urls",[]),
                "warm_paths": inv.get("warm_paths",[]),
            },
            "score": inv["_score"],
            "email_draft": None,
        })

    # exports still work; CSV will just have empty email unless user generated it
    export_results = {}
    if "csv" in exports:   export_results["csv"] = export_csv(matches)
    if "pdf" in exports:   export_results["pdf"] = export_pdf(brief, matches)
    if "notion" in exports: export_results["notion"] = export_notion(brief, matches)

    return matches, export_results, one_pager_md(brief, matches)
