from fastapi import FastAPI
from .schemas import GenerateRequest, GenerateResponse, GenerateEmailRequest, GenerateEmailResponse
from .orchestrator import run_pipeline
from .db import init_db
from .agents.writer import run as write_one

app = FastAPI(title="Fundraise Copilot (on-demand emails)")

@app.on_event("startup")
def _startup():
    init_db()

@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        matches, export_results, _ = run_pipeline(
            brief=req.brief.model_dump(),
            top_k=req.top_k,
            use_llm=req.use_llm,
            allow_scrape=req.allow_scrape,
            exports=req.exports
        )
    except Exception:
        matches, export_results = [], {}
    out_matches = []
    for m in matches:
        inv, sc = m["investor"], m["score"]
        out_matches.append({
            "investor": inv,
            "fit_score": sc["fit_score"],
            "stage_fit": sc["stage_fit"],
            "sector_fit": sc["sector_fit"],
            "geo_fit": sc["geo_fit"],
            "momentum": sc["momentum"],
            "rationale": sc["rationale"],
            "email_draft": m.get("email_draft"),
        })
    return {"matches": out_matches, "exports": export_results}

# NEW: per-investor email generation
@app.post("/api/generate_email", response_model=GenerateEmailResponse)
def generate_email(req: GenerateEmailRequest):
    try:
        # build the minimal score dict used by writer's rationale
        score_stub = {"rationale": "Context fit based on your brief."}
        email = write_one(req.investor.model_dump(), score_stub, req.brief.model_dump(), use_llm=req.use_llm)
    except Exception:
        email = "Hi — quick intro; we're building something relevant to your thesis. Could we grab 15 minutes next week?"
    return {"email_draft": email}
