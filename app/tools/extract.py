import re
from typing import List

def recent_highlights(text: str, max_items: int = 3) -> List[str]:
    if not text:
        return []
    cands = re.split(r"(?<=[.!?])\s+", text)[:60]
    hits = [s.strip() for s in cands if re.search(r"\b(invest|fund|raised|\$|AI|ML)\b", s, re.I)]
    return hits[:max_items]
