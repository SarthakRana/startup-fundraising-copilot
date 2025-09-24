import re
import requests
import trafilatura
from urllib.parse import urlparse
from ..config import ALLOWED_DOMAINS

def allowed(url: str) -> bool:
    if not ALLOWED_DOMAINS:
        return True
    host = urlparse(url).netloc
    return any(host.endswith(dom) for dom in ALLOWED_DOMAINS)

def fetch_text(url: str) -> str:
    if not allowed(url):
        return ""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        downloaded = trafilatura.extract(r.text, include_comments=False, include_tables=False) or ""
        return re.sub(r"\s+", " ", downloaded).strip()
    except Exception:
        return ""
