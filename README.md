# Startup Fundraising Copilot (Gemini + Postgres)

Multi-agent (Researcher → Matchmaker → Writer) fundraising helper:
- Finds relevant investors (seed dataset, optional light scraping)
- Scores fit transparently
- Drafts tailored outreach emails with **Google Gemini**
- Exports to **CSV**, **PDF**, and/or **Notion**

## Stack
- Streamlit UI
- FastAPI backend
- Google Gemini (emails; fallback template if no key)
- PostgreSQL (investors/matches cache)
- ReportLab (PDF), Notion SDK (Notion pages)

## Prereqs
- Python 3.10+
- PostgreSQL running locally (or remote)
- (Optional) Google API key for Gemini
- (Optional) Notion integration + parent page

## Setup

```bash
git clone <this-repo>
cd fundraise-copilot

python3 -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env to set PG*, GOOGLE_API_KEY, and (optional) NOTION_*.
