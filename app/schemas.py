from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import List, Optional, Literal

_CANON_STAGES = {
    "angel": "angel",
    "preseed": "pre-seed",
    "pre-seed": "pre-seed",
    "pre seed": "pre-seed",
    "seed": "seed",
    "seed+": "seed+",
    "seed plus": "seed+",
    "seed extension": "seed+",
    "pre series a": "pre-series-a",
    "pre-series-a": "pre-series-a",
    "series a": "series-a",
    "series-a": "series-a",
    "series b": "series-b",
    "series-b": "series-b",
    "series c": "series-c",
    "series-c": "series-c",
}

def _normalize_stage(v: str) -> str:
    v = (v or "").strip().lower().replace("_", " ").replace("/", " ")
    v = v.replace("-", " ")
    return _CANON_STAGES.get(v, v.replace(" ", "-"))

class StartupBrief(BaseModel):
    name: str = Field(default="", description="Startup name")
    one_liner: str = ""
    sector: List[str] = []
    stage: str = ""
    round_size_usd: Optional[float] = None
    geo: Optional[str] = None
    traction: List[str] = []
    ask: str = "Raising intro meetings with aligned investors."

    @field_validator("stage")
    @classmethod
    def stage_normalize(cls, v: str) -> str:
        return _normalize_stage(v)

    @field_validator("sector")
    @classmethod
    def sector_normalize(cls, v: List[str]) -> List[str]:
        return [s.strip().lower() for s in v if s.strip()]

class Investor(BaseModel):
    name: str
    fund: str
    stages: List[str]
    sectors: List[str]
    check_min: Optional[float] = None
    check_max: Optional[float] = None
    geo: Optional[str] = None
    notable_investments: List[str] = []
    recent_news: List[str] = []
    urls: List[str] = []
    warm_paths: List[str] = []

class Match(BaseModel):
    investor: Investor
    fit_score: float
    stage_fit: float
    sector_fit: float
    geo_fit: float
    momentum: float
    rationale: str
    email_draft: Optional[str] = None

ExportKind = Literal["csv", "pdf", "notion"]

class GenerateRequest(BaseModel):
    brief: StartupBrief
    top_k: int = 25
    use_llm: bool = True          # now ignored for batch (emails are on-demand)
    allow_scrape: bool = False
    exports: List[ExportKind] = ["csv"]

    @field_validator("brief")
    @classmethod
    def require_sector_and_stage(cls, brief: StartupBrief, info: ValidationInfo):
        if not brief.sector:
            raise ValueError("Please select at least one sector.")
        if not brief.stage:
            raise ValueError("Please select a stage.")
        return brief

class GenerateResponse(BaseModel):
    matches: List[Match]
    exports: dict

# NEW: single-email generation
class GenerateEmailRequest(BaseModel):
    brief: StartupBrief
    investor: Investor
    use_llm: bool = True

class GenerateEmailResponse(BaseModel):
    email_draft: str
