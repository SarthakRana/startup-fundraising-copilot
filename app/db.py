import psycopg2
from .config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

def get_conn():
    return psycopg2.connect(
        host=PGHOST, port=PGPORT, dbname=PGDATABASE, user=PGUSER, password=PGPASSWORD
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS investors (
        id SERIAL PRIMARY KEY,
        name TEXT,
        fund TEXT,
        stages TEXT,
        sectors TEXT,
        check_min DOUBLE PRECISION,
        check_max DOUBLE PRECISION,
        geo TEXT,
        notable_investments TEXT,
        recent_news TEXT,
        urls TEXT,
        warm_paths TEXT,
        unique_key TEXT UNIQUE
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY,
        investor_id INTEGER REFERENCES investors(id),
        fit_score DOUBLE PRECISION,
        stage_fit DOUBLE PRECISION,
        sector_fit DOUBLE PRECISION,
        geo_fit DOUBLE PRECISION,
        momentum DOUBLE PRECISION,
        rationale TEXT,
        email_draft TEXT
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
