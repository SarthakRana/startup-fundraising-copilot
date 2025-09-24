from ..tools.llm_gemini import draft_email_gemini

def run(investor: dict, score: dict, brief: dict, use_llm: bool = True) -> str:
    rationale = (
        f"{investor.get('fund')} invests at {', '.join(investor.get('stages', []))} "
        f"in {', '.join(investor.get('sectors', []))}. {score.get('rationale','Thesis alignment.')} "
    )
    return draft_email_gemini(
        investor.get("name","Investor"),
        investor.get("fund","Fund"),
        rationale,
        brief,
        allow_llm=use_llm
    )
