import google.generativeai as genai
from ..config import GOOGLE_API_KEY

def gemini_available() -> bool:
    return bool(GOOGLE_API_KEY)

def _fallback_email(investor_name, fund, rationale, brief):
    traction = "; ".join(brief.get("traction", [])[:2]) or "early traction with design partners"
    return (
        f"Subject: Intro — {brief['name']} × {fund}\n\n"
        f"Hi {investor_name.split()[0]},\n\n"
        f"I'm building {brief['name']} — {brief['one_liner']}.\n"
        f"Why you: {rationale}\n\n"
        f"Quick hits: {traction}.\n"
        f"We're raising {brief.get('round_size_usd','a seed round')}.\n"
        f"Open to a 15-min intro next week?\n\n"
        f"— {brief['name']} team"
    )

def draft_email_gemini(investor_name: str, fund: str, rationale: str, brief: dict, allow_llm: bool = True) -> str:
    if not (allow_llm and gemini_available()):
        return _fallback_email(investor_name, fund, rationale, brief)
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
            Write a concise 100–120 word intro email to {investor_name} at {fund}.
            Startup brief: {brief}
            Reason to contact (rationale): {rationale}
            Tone: warm, direct, specific. Include one traction point if available. Ask for a 15-minute intro next week.
            Return plain text only.
        """
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        return text or _fallback_email(investor_name, fund, rationale, brief)
    except Exception:
        return _fallback_email(investor_name, fund, rationale, brief)
