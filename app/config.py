import os
from dotenv import load_dotenv

load_dotenv()

# LLM
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Search/scrape
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
ALLOWED_DOMAINS = [d.strip() for d in os.getenv("ALLOWED_DOMAINS", "").split(",") if d.strip()]

# Postgres
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "fundraise_copilot")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")

# Notion
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")

# LLM budget (per /api/generate run)
LLM_EMAIL_BUDGET = int(os.getenv("LLM_EMAIL_BUDGET", "5"))

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "app", "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)
