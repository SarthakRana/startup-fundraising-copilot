import os, time, threading, requests
import streamlit as st
import pandas as pd
from urllib.parse import urlparse

API_BASE = os.getenv("COPILOT_API_URL_BASE", "http://127.0.0.1:8000")
API_GENERATE = f"{API_BASE}/api/generate"
API_EMAIL = f"{API_BASE}/api/generate_email"

st.set_page_config(page_title="Fundraise Copilot", layout="wide")
st.title("🚀 Startup Fundraising Copilot")

# ---------- Clean, compact styling ----------
st.markdown("""
<style>
:root { --card-bg:#ffffff; --border:#e5e7eb; --shadow:0 2px 8px rgba(0,0,0,0.06); --muted:#6b7280; --chip:#f3f4f6; --pill-bg:#eef2ff; --pill-fg:#1d4ed8; }
@media (prefers-color-scheme: dark) {
  :root { --card-bg:#0f1522; --border:#202636; --shadow:0 2px 10px rgba(0,0,0,0.35); --muted:#9aa4b2; --chip:#1d2433; --pill-bg:#1a2240; --pill-fg:#93b4ff; }
}
.card { background:var(--card-bg); border:1px solid var(--border); border-radius:14px; padding:14px 16px; margin:10px 0 14px 0; box-shadow:var(--shadow);}
.card h3 { margin:0 0 6px 0; font-size:18px; line-height:1.2;}
.meta { color:var(--muted); font-size:12px; margin-bottom:6px;}
.badge { display:inline-block; padding:3px 8px; border-radius:999px; background:var(--chip); margin:0 6px 6px 0; font-size:11px;}
.pill  { display:inline-block; padding:3px 8px; border-radius:999px; background:var(--pill-bg); color:var(--pill-fg); font-weight:600; font-size:11px;}
.divider { border:none; border-top:1px solid var(--border); margin:10px 0;}
.kv { margin:4px 0 2px 0; }
.kv b { width:60px; display:inline-block; }
.rightcol { display:flex; gap:8px; justify-content:flex-end; align-items:center; }
</style>
""", unsafe_allow_html=True)

def domain(u: str) -> str:
    try:
        return urlparse(u).netloc.replace("www.","")
    except Exception:
        return u

def run_pipeline(payload, out: dict, err: dict):
    try:
        r = requests.post(API_GENERATE, json=payload, timeout=180)
        r.raise_for_status()
        out["data"] = r.json()
    except Exception as e:
        err["error"] = str(e)

def matches_to_df(matches):
    rows=[]
    for i,m in enumerate(matches, start=1):
        inv=m["investor"]
        rows.append({"Rank":i,"Investor":inv["name"],"Fund":inv["fund"],"Score":m["fit_score"],
                     "Stage fit":m["stage_fit"],"Sector fit":m["sector_fit"],
                     "Geo fit":m["geo_fit"],"Momentum":m["momentum"],"Why now":m["rationale"]})
    return pd.DataFrame(rows)

# ====== INPUTS ======
st.subheader("Your Startup Brief")

SECTOR_OPTIONS = [
    "ai","agents","llm infra","ml ops","infrastructure","security","cybersecurity","privacy",
    "developer tools","devops","saas","data","analytics","bi","fintech","payments","defi","crypto",
    "healthcare","biotech","medtech","digital health","climate","energy","carbon","robotics",
    "hardware","semiconductors","iot","edge","aerospace","space","mobility","autonomy",
    "ecommerce","marketplaces","consumer","social","creator economy","media","gaming",
    "edtech","proptech","legaltech","hr tech","martech","supply chain","logistics","govtech"
]
STAGE_OPTIONS = ["angel","pre-seed","seed","seed+","pre-series-a","series-a","series-b","series-c"]

colA, colB = st.columns([1.2, 1])
with colA:
    name = st.text_input("Startup Name", value="", placeholder="e.g., IncidentDesk AI")
    one_liner = st.text_area("One-liner", value="", placeholder="Short description in one sentence")
    sector = st.multiselect("Sector tags *", SECTOR_OPTIONS, default=[])  # REQUIRED
    traction = st.text_area("Traction bullets (one per line)", value="")
with colB:
    stage = st.selectbox("Stage *", [""] + STAGE_OPTIONS, index=0)        # REQUIRED
    geo = st.text_input("Geo", value="", placeholder="e.g., US")
    round_size = st.number_input("Round size (USD)", min_value=0, value=0, step=100000)
    ask = st.text_input("Ask", value="Raising intro meetings with aligned investors.")
    top_k = st.slider("Top K investors", 5, 50, 20)

st.markdown("### Options")
opt2, opt3 = st.columns([1,2])
with opt2:
    allow_scrape = st.checkbox("Enrich with light scraping (optional)", value=False)
with opt3:
    export_opts = st.multiselect("Export to", ["csv","pdf","notion"], default=["csv"])

valid = (len(sector)>0) and ((stage or "").strip()!="")
if not valid:
    st.warning("**Sector** and **Stage** are required to enable **Generate**.")

generate = st.button("🔮 Generate Targets", type="primary", use_container_width=True, disabled=not valid)

if generate:
    payload = {
        "brief":{
            "name":name.strip(),
            "one_liner":one_liner.strip(),
            "sector":sector,
            "stage":(stage or "").strip().lower(),
            "round_size_usd": round_size if round_size>0 else None,
            "geo":geo.strip(),
            "traction":[t.strip() for t in traction.splitlines() if t.strip()],
            "ask":ask.strip()
        },
        "top_k":top_k,
        "use_llm":False,        # on-demand emails now
        "allow_scrape":allow_scrape,
        "exports":export_opts
    }
    res, err = {}, {}
    t = threading.Thread(target=run_pipeline, args=(payload,res,err))
    t.start()
    with st.status("Running pipeline…", expanded=True) as s:
        for msg in ["🔎 Researcher…","🧮 Matchmaker…","✉️ Writer (on-demand)…"]:
            st.write(msg); time.sleep(0.2)
        t.join()
        if err.get("error"):
            s.update(label="❌ Error", state="error"); st.error(err["error"])
        else:
            s.update(label="✅ Complete", state="complete")
            st.session_state["results"] = res.get("data", {})
            # Save current brief for on-demand email calls
            st.session_state["brief_for_email"] = payload["brief"]

# ====== RESULTS ======
st.write(""); st.markdown("---"); st.header("🏁 Results")

data = st.session_state.get("results")
if not data:
    st.info("Generate targets first, then create emails per investor.")
else:
    matches = data.get("matches", [])
    exports = data.get("exports", {})

    c1,c2,c3,c4 = st.columns(4)
    total=len(matches); avg= round(sum(m["fit_score"] for m in matches)/total,1) if total else 0
    top_fund = matches[0]["investor"]["fund"] if total else "—"
    exported = " • ".join([x for x in ["CSV" if exports.get("csv") else "", "PDF" if exports.get("pdf") else "", "Notion" if exports.get("notion") else ""] if x])
    with c1: st.metric("Total matches", total)
    with c2: st.metric("Average score", avg)
    with c3: st.metric("Top-ranked fund", top_fund)
    with c4: st.metric("Exports", exported or "None")
    if exported:
        links=[]
        if exports.get("csv"): links.append(f"CSV: `{exports['csv']}`")
        if exports.get("pdf"): links.append(f"PDF: `{exports['pdf']}`")
        if exports.get("notion"): links.append(f"[Notion Page]({exports['notion']})")
        st.markdown("**Download / Links:** " + " • ".join(links))

    st.write(""); st.subheader("Ranked Investors (sortable table)")
    st.dataframe(matches_to_df(matches), use_container_width=True, hide_index=True)

    # ----- Detailed Cards (single-button flow; compact) -----
    if "emails" not in st.session_state: st.session_state["emails"] = {}
    if "visible" not in st.session_state: st.session_state["visible"] = {}

    @st.fragment
    def render_cards():
        st.write(""); st.subheader("Detailed Cards")
        for i, m in enumerate(matches, start=1):
            inv = m["investor"]
            key = f"{inv.get('name','')}-{inv.get('fund','')}-{i}"
            email_text = st.session_state["emails"].get(key)
            visible = st.session_state["visible"].get(key, False)

            st.markdown('<div class="card">', unsafe_allow_html=True)

            # Header row: left title/meta; right controls
            hL, hR = st.columns([5, 2])
            with hL:
                st.markdown(f"<h3>{i}. {inv['name']} — {inv['fund']}</h3>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='meta'><span class='pill'>Score {m['fit_score']}</span>&nbsp;&nbsp;"
                    f"Why now: <i>{m['rationale']}</i></div>",
                    unsafe_allow_html=True
                )
            with hR:
                use_llm = st.checkbox("Use Gemini for email", value=True, key=f"use_llm_{key}")
                # Single button: if no email -> generate & show; if already visible -> hide; if generated but hidden -> show
                label = "Generate email" if email_text is None else ("Hide email" if visible else "Show email")
                if st.button(label, key=f"btn_{key}", use_container_width=True):
                    if email_text is None:
                        # generate
                        try:
                            brief = st.session_state.get("brief_for_email") or {
                                "name": st.session_state.get("name",""),
                                "one_liner": st.session_state.get("one_liner",""),
                                "sector": st.session_state.get("sector",[]),
                                "stage": st.session_state.get("stage",""),
                                "round_size_usd": st.session_state.get("round_size_usd"),
                                "geo": st.session_state.get("geo",""),
                                "traction": st.session_state.get("traction",[]),
                                "ask": st.session_state.get("ask","")
                            }
                            payload = {"brief": brief, "investor": inv, "use_llm": use_llm}
                            r = requests.post(API_EMAIL, json=payload, timeout=60)
                            r.raise_for_status()
                            st.session_state["emails"][key] = r.json().get("email_draft","")
                            st.session_state["visible"][key] = True
                        except Exception as e:
                            st.error(f"Failed to generate email: {e}")
                    else:
                        # toggle
                        st.session_state["visible"][key] = not visible
                    st.rerun()

            st.markdown("<hr class='divider'/>", unsafe_allow_html=True)

            cL, cR = st.columns([2,1])
            with cL:
                s_badges = " ".join([f"<span class='badge'>{s}</span>" for s in inv.get('stages', [])])
                sec_badges = " ".join([f"<span class='badge'>{s}</span>" for s in inv.get('sectors', [])])
                st.markdown(f"<div class='kv'><b>Stages:</b> {s_badges}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kv'><b>Sectors:</b> {sec_badges}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kv'><b>Geo:</b> {inv.get('geo','—')}</div>", unsafe_allow_html=True)
                if inv.get("notable_investments"):
                    st.markdown("**Notable:** " + ", ".join(inv["notable_investments"]))
                if inv.get("urls"):
                    links = " ".join([f"<a href='{u}' target='_blank'>{domain(u)}</a>" for u in inv["urls"]])
                    st.markdown("**Links:** " + links, unsafe_allow_html=True)
                if inv.get("warm_paths"):
                    st.markdown("**Warm paths:** " + ", ".join(inv["warm_paths"]))
            with cR:
                if st.session_state["visible"].get(key, False) and st.session_state["emails"].get(key):
                    st.markdown("**Email draft**")
                    st.code(st.session_state["emails"][key], language="markdown")
                elif st.session_state["visible"].get(key, False):
                    st.caption("Generating…")
                else:
                    st.caption("Click **Generate email** to create a draft.")

            st.markdown("</div>", unsafe_allow_html=True)

    render_cards()
